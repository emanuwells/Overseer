from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import require_service_token
from ..builders.payload import build_details, build_full, build_ops_fast, build_ops_heavy

router = APIRouter(prefix="/v1/monitoring", tags=["monitoring"])


@router.get("/full", dependencies=[Depends(require_service_token)])
def monitoring_full() -> dict:
    return build_full()


@router.get("/details", dependencies=[Depends(require_service_token)])
def monitoring_details() -> dict:
    return build_details()


@router.get("/ops/fast")
def monitoring_ops_fast() -> dict:
    return build_ops_fast(build_full())


@router.get("/ops/heavy")
def monitoring_ops_heavy() -> dict:
    return build_ops_heavy(build_full())
