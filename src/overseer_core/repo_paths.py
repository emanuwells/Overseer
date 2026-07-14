"""Resolução da raiz do repositório Overseer (local, Docker, testes)."""

from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    if env_root := os.getenv("OVERSEER_ROOT"):
        return Path(env_root)
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "frontend").is_dir() and (parent / "src" / "pyproject.toml").is_file():
            return parent
    return here.parents[2]
