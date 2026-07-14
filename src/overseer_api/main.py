from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterator
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from overseer_core.repo_paths import repo_root
from overseer_core.slack_digest import DIGEST_TZ, digest_enabled, next_digest_at, send_daily_digest
from overseer_core.store import init_schema

ROOT = repo_root()

from .routers import catalog, events, health, orchestrate, read

FRONTEND_DIR = ROOT / "frontend"
API_VERSION = "5.6.0"

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


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_schema()
    digest_task = asyncio.create_task(_slack_digest_loop())
    try:
        yield
    finally:
        digest_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await digest_task


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
        return RedirectResponse(url="/ui/dashboard.html", status_code=307)

    @app.get("/ui")
    def ui_root() -> RedirectResponse:
        return RedirectResponse(url="/ui/dashboard.html", status_code=307)

    if FRONTEND_DIR.is_dir():
        app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="ui")

    return app


app = create_app()
