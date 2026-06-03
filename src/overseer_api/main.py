from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .routers import health, monitoring, pipelines, runners, triggers

WEBAPP_DIR = ROOT / "webapp"


def create_app() -> FastAPI:
    app = FastAPI(
        title="Overseer API",
        version="3.2.0",
        description="Canonical HTTP API for pipeline monitoring and orchestration.",
    )

    origins = os.getenv("OVERSEER_CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(monitoring.router)
    app.include_router(triggers.router)
    app.include_router(pipelines.router)
    app.include_router(runners.router)

    if WEBAPP_DIR.is_dir():
        app.mount("/ui", StaticFiles(directory=str(WEBAPP_DIR), html=True), name="ui")

    @app.get("/")
    def root() -> dict:
        return {
            "service": "overseer-api",
            "version": "3.2.0",
            "docs": "/docs",
            "ui": "/ui/" if WEBAPP_DIR.is_dir() else None,
        }

    return app


app = create_app()
