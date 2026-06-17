"""Utilitários partilhados entre módulos overseer_core."""

from __future__ import annotations

import os
from typing import Any

_TRUTHY = frozenset({"1", "true", "yes", "on"})
_FALSY = frozenset({"0", "false", "no", "off"})


def env_flag(name: str, default: bool = False) -> bool:
    """Interpreta uma variável de ambiente como booleano.

    Valores reconhecidos como ``True``: ``1``, ``true``, ``yes``, ``on``.
    Valores reconhecidos como ``False``: ``0``, ``false``, ``no``, ``off``.
    Variável vazia ou ausente devolve ``default``.
    """
    raw = os.getenv(name, "").strip().lower()
    if raw in _TRUTHY:
        return True
    if raw in _FALSY:
        return False
    return default


def safe_metadata(row: dict[str, Any], key: str = "metadata") -> dict[str, Any]:
    """Extrai um sub-dicionário de *row* com validação de tipo.

    Devolve ``{}`` quando o valor é ``None`` ou não é ``dict``.
    """
    value = row.get(key)
    if isinstance(value, dict):
        return value
    return {}
