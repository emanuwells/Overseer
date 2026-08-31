from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import AsyncIterator
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

from overseer_core.repo_paths import repo_root
from overseer_core.slack_digest import DIGEST_TZ, digest_enabled, next_digest_at, send_daily_digest
from overseer_core.store import (
    auto_purge_retention_if_due,
    init_schema,
    retention_poll_seconds,
)

ROOT = repo_root()

from .routers import catalog, events, health, orchestrate, read

FRONTEND_DIST = ROOT / "frontend" / "dist"
API_VERSION = "5.8.39"

logger = logging.getLogger("overseer.api")


async def _slack_digest_loop() -> None:
    while True:
        if not digest_enabled():
            await asyncio.sleep(3600)
            continue

        now = datetime.now(DIGEST_TZ)
        target = next_digest_at(now)
        wait_sec = max(60.0, (target - now).total_seconds())
        await asyncio.sleep(wait_sec)

        try:
            sent = await asyncio.to_thread(send_daily_digest)
            if sent:
                logger.info("Digest Slack enviado às %s", datetime.now(DIGEST_TZ).isoformat())
        except Exception:
            logger.exception("Falha no digest Slack agendado")


async def _apply_retention_if_due() -> None:
    try:
        retention = await asyncio.to_thread(auto_purge_retention_if_due)
        if retention:
            logger.info("Retenção automática aplicada: %s", retention)
    except Exception:
        logger.exception("Falha na retenção automática")


async def _retention_loop() -> None:
    """Verifica a retenção de hora a hora; o marcador limita a purga a uma vez por dia."""
    while True:
        await asyncio.sleep(retention_poll_seconds())
        await _apply_retention_if_due()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_schema()
    await _apply_retention_if_due()
    retention_task = asyncio.create_task(_retention_loop())
    digest_task = asyncio.create_task(_slack_digest_loop())
    try:
        yield
    finally:
        retention_task.cancel()
        digest_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await retention_task
        with contextlib.suppress(asyncio.CancelledError):
            await digest_task


def _spa_index() -> FileResponse:
    index = FRONTEND_DIST / "index.html"
    if not index.is_file():
        raise HTTPException(status_code=404, detail="Frontend não construído.")
    return FileResponse(index)


def _spa_file(relative: str) -> FileResponse:
    candidate = (FRONTEND_DIST / relative).resolve()
    dist_root = FRONTEND_DIST.resolve()
    if not str(candidate).startswith(str(dist_root)):
        raise HTTPException(status_code=404)
    if candidate.is_file():
        return FileResponse(candidate)
    return _spa_index()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Overseer API",
        version=API_VERSION,
        description="API canónica para observabilidade de pipelines e DAGs.",
        lifespan=lifespan,
    )

    origins = os.getenv("OVERSEER_CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin.strip() for origin in origins if origin.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(read.router)
    app.include_router(events.router)
    app.include_router(catalog.router)
    app.include_router(orchestrate.router)

    @app.get("/")
    def root() -> RedirectResponse:
        return RedirectResponse(url="/ui/", status_code=307)

    @app.get("/ui")
    def ui_root() -> RedirectResponse:
        return RedirectResponse(url="/ui/", status_code=307)

    if FRONTEND_DIST.is_dir():

        @app.get("/ui/")
        def ui_index() -> FileResponse:
            return _spa_index()

        @app.get("/ui/{rest:path}")
        def ui_spa(rest: str) -> FileResponse:
            return _spa_file(rest)

    return app


app = create_app()
