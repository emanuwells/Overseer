from __future__ import annotations

import hmac
import logging
import os
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)
_logger = logging.getLogger("overseer.auth")
_token_warning_emitted = False

PUBLIC_PATH_PREFIXES = (
    "/v1/health",
    "/ui",
)


def api_token() -> str:
    return (os.getenv("OVERSEER_API_TOKEN") or "").strip()


def require_service_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer)],
) -> None:
    expected = api_token()
    if not expected:
        global _token_warning_emitted
        if not _token_warning_emitted:
            _logger.warning(
                "OVERSEER_API_TOKEN is not set — all endpoints are unprotected. "
                "Set this variable in production.",
            )
            _token_warning_emitted = True
        return
    if credentials is None or not hmac.compare_digest(
        credentials.credentials.encode(), expected.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API token.",
        )
