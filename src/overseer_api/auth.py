from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)

PUBLIC_PATH_PREFIXES = (
    "/v1/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/ui",
)


def api_token() -> str:
    return (os.getenv("OVERSEER_API_TOKEN") or "").strip()


def require_service_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer)],
) -> None:
    expected = api_token()
    if not expected:
        return
    if credentials is None or credentials.credentials != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token.",
        )
