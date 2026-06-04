from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.overseer_core.store import init_schema

from .routers import events, health, orchestrate, read

WEBAPP_DIR = ROOT / "webapp" / "dist"
WEBAPP_FALLBACK_DIR = ROOT / "webapp"
API_VERSION = "4.0.0"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_schema()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Overseer API",
        version=API_VERSION,
        description="API canónica para leitura, ingest e orquestração de pipelines.",
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
    app.include_router(orchestrate.router)

    ui_dir = WEBAPP_DIR if WEBAPP_DIR.is_dir() else WEBAPP_FALLBACK_DIR
    if ui_dir.is_dir():
        app.mount("/ui", StaticFiles(directory=str(ui_dir), html=True), name="ui")

    @app.get("/")
    def root() -> dict:
        return {
            "service": "overseer-api",
            "version": API_VERSION,
            "health": "/v1/health",
            "read_api": "/v1/read/overview",
            "write_api": "/v1/events/runs/start",
            "orchestrate_api": "/v1/orchestrate/triggers",
            "docs": "/docs",
            "ui": "/ui/",
        }

    return app


app = create_app()
