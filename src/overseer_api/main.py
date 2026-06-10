from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from overseer_core.store import init_schema

ROOT = Path(__file__).resolve().parents[2]

from .routers import catalog, events, health, monitoring, orchestrate, read

FRONTEND_DIR = ROOT / "frontend"
API_VERSION = "5.1.0"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_schema()
    yield


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
    app.include_router(monitoring.router)
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
