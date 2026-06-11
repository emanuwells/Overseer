#!/usr/bin/env python3
"""Provisiona manifests e wrappers de runner a partir do catálogo YAML.

Suporta Linux (run.sh + crontab) e Windows (run.ps1 + Task Scheduler). Em
ambientes multi-host, o ``host_id`` vai no manifest/metadata e na coluna
``host_id`` da API — o ``pipeline_id`` mantém-se lógico (ex. ``medidata_pipeline``).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import tempfile

import yaml

RUN_SH_TEMPLATE = """#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
set -a
[ -f "$HERE/../.env.overseer" ] && source "$HERE/../.env.overseer"
[ -f "$HERE/.env.overseer" ] && source "$HERE/.env.overseer"
set +a
OVERSEER_VENV="${{OVERSEER_VENV:-{venv}}}"
REQUESTED_BY="${{OVERSEER_REQUESTED_BY:-cron}}"
"$OVERSEER_VENV/bin/overseer-agent" manifest "$HERE/manifest.yaml" --by "$REQUESTED_BY"
"""

RUN_PS1_TEMPLATE = """$ErrorActionPreference = "Stop"
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Import-EnvFile {{
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {{ return }}
    foreach ($raw in Get-Content -LiteralPath $Path) {{
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith("#") -or ($line -notmatch "=")) {{ continue }}
        $key, $value = $line.Split("=", 2)
        [Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
    }}
}}

Import-EnvFile (Join-Path $Here "..\\.env.overseer")
Import-EnvFile (Join-Path $Here ".env.overseer")

$env:NO_PROXY = "127.0.0.1,localhost"
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""

$Venv = $env:OVERSEER_VENV
if (-not $Venv) {{ $Venv = "{venv}" }}
$Python = Join-Path $Venv "Scripts\\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {{
    throw "Python do venv não encontrado em $Python"
}}
if (-not $env:OVERSEER_API_URL) {{
    throw "OVERSEER_API_URL em falta. Verifica ..\\.env.overseer"
}}

$RequestedBy = $env:OVERSEER_REQUESTED_BY
if (-not $RequestedBy) {{ $RequestedBy = "taskscheduler" }}
& $Python -m overseer_agent manifest (Join-Path $Here "manifest.yaml") --by $RequestedBy
exit $LASTEXITCODE
"""


def load_env_file(path: pathlib.Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    env: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def normalize_host_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-")


def resolve_platform(value: str) -> str:
    if value == "auto":
        return "windows" if os.name == "nt" else "linux"
    return value


def default_venv(platform: str) -> str:
    if platform == "windows":
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(base, "overseer-venv")
    return os.path.expanduser("~/overseer-venv")


def resolve_host_id(arg_value: str, runner_env: dict[str, str]) -> str:
    """Devolve o host_id efetivo, ou string vazia se não deve aplicar sufixo."""
    if arg_value and arg_value != "auto":
        return normalize_host_id(arg_value)
    if arg_value == "auto":
        candidate = runner_env.get("OVERSEER_HOST_ID") or socket.gethostname()
        return normalize_host_id(candidate)
    # Sem --host-id: comportamento legado (sem sufixo).
    return ""


def default_repo_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def runners_catalog_dir(repo_root: pathlib.Path | None = None) -> pathlib.Path:
    return (repo_root or default_repo_root()) / "deploy" / "runners"


def list_runner_catalogs(repo_root: pathlib.Path | None = None) -> list[pathlib.Path]:
    catalog_dir = runners_catalog_dir(repo_root)
    if not catalog_dir.is_dir():
        return []
    return sorted(
        path
        for path in catalog_dir.glob("*.yaml")
        if path.is_file() and not path.name.startswith("_")
    )


def resolve_runner_catalog(
    *,
    explicit: str | None = None,
    runners_root: pathlib.Path | None = None,
    repo_root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Resolve deploy/runners/<host>.yaml para este host."""
    root = repo_root or default_repo_root()
    catalog_dir = runners_catalog_dir(root)

    if explicit:
        catalog_path = pathlib.Path(explicit).expanduser()
        if not catalog_path.is_absolute():
            catalog_path = (pathlib.Path.cwd() / catalog_path).resolve()
        if not catalog_path.is_file():
            raise FileNotFoundError(f"Catálogo não encontrado: {catalog_path}")
        return catalog_path

    env_catalog = os.environ.get("OVERSEER_RUNNERS_CATALOG", "").strip()
    if env_catalog:
        catalog_path = pathlib.Path(env_catalog).expanduser()
        if not catalog_path.is_absolute():
            catalog_path = (pathlib.Path.cwd() / catalog_path).resolve()
        if not catalog_path.is_file():
            raise FileNotFoundError(f"OVERSEER_RUNNERS_CATALOG inválido: {catalog_path}")
        return catalog_path

    runners_root = runners_root or pathlib.Path(os.path.expanduser("~/overseer-runners"))
    runner_env = load_env_file(runners_root / ".env.overseer")

    candidates: list[str] = []
    for key in (runner_env.get("OVERSEER_HOST_ID", ""), socket.gethostname()):
        if not key:
            continue
        normalized = normalize_host_id(key)
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    for host_key in candidates:
        catalog_path = catalog_dir / f"{host_key}.yaml"
        if catalog_path.is_file():
            return catalog_path

    available = [path.name for path in list_runner_catalogs(root)]
    tried = ", ".join(f"{name}.yaml" for name in candidates) or "(nenhum)"
    available_text = ", ".join(available) if available else "(nenhum)"
    raise FileNotFoundError(
        "Catálogo não encontrado para este host. "
        f"Tentado: {tried}. Disponíveis em deploy/runners/: {available_text}. "
        "Cria deploy/runners/<hostname>.yaml ou define OVERSEER_RUNNERS_CATALOG."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--catalog",
        default="",
        help="Caminho para o catálogo YAML. Omitir para auto: deploy/runners/<host>.yaml",
    )
    parser.add_argument("--repo-root", default="", help="Raiz do repo Overseer (auto-detect por defeito).")
    parser.add_argument("--runners-root", default=os.path.expanduser("~/overseer-runners"))
    parser.add_argument("--platform", choices=["linux", "windows", "auto"], default="auto")
    parser.add_argument("--venv", default="")
    parser.add_argument(
        "--host-id",
        default="",
        help="Sufixo do pipeline_id por máquina. 'auto' usa OVERSEER_HOST_ID ou o hostname.",
    )
    parser.add_argument("--env-file", default="")
    parser.add_argument("--register", action="store_true")
    parser.add_argument(
        "--catalog-json-out",
        default=os.path.join(tempfile.gettempdir(), "overseer_runner_catalog.json"),
    )
    args = parser.parse_args()

    platform = resolve_platform(args.platform)
    venv = pathlib.Path(args.venv).expanduser() if args.venv else pathlib.Path(default_venv(platform))
    agent = venv / ("Scripts/overseer-agent.exe" if platform == "windows" else "bin/overseer-agent")

    repo_root = pathlib.Path(args.repo_root).expanduser() if args.repo_root else default_repo_root()
    runners_root = pathlib.Path(args.runners_root).expanduser()
    runners_root.mkdir(parents=True, exist_ok=True)

    catalog_path = resolve_runner_catalog(
        explicit=args.catalog or None,
        runners_root=runners_root,
        repo_root=repo_root,
    )
    print(f"Catálogo: {catalog_path}")

    if args.env_file and pathlib.Path(args.env_file).is_file():
        src_env = load_env_file(pathlib.Path(args.env_file))
        token = src_env.get("OVERSEER_API_TOKEN", "")
        api_url = src_env.get("OVERSEER_API_URL", "http://127.0.0.1:8090")
        host_id = src_env.get("OVERSEER_HOST_ID", "")
        runners_root.joinpath(".env.overseer").write_text(
            f"OVERSEER_API_URL={api_url}\n"
            f"OVERSEER_API_TOKEN={token}\n"
            f"OVERSEER_HOST_ID={host_id}\n",
            encoding="utf-8",
        )
        if os.name != "nt":
            os.chmod(runners_root / ".env.overseer", 0o600)

    runner_env = load_env_file(runners_root / ".env.overseer")
    host_id = resolve_host_id(args.host_id, runner_env)

    catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    pipelines = catalog.get("pipelines") or []
    created: list[dict] = []

    for item in pipelines:
        logical_id = str(item["id"])
        dest = runners_root / logical_id
        dest.mkdir(parents=True, exist_ok=True)

        metadata: dict = {"os": platform}
        if host_id:
            metadata["host_id"] = host_id

        manifest = {
            "pipeline_id": logical_id,
            "pipeline_name": item.get("name", logical_id),
            "owner": item.get("owner", "data"),
            "criticality": item.get("criticality", "medium"),
            "schedule": item.get("schedule", "manual"),
            "metadata": metadata,
            "steps": item["steps"],
        }
        dest.joinpath("manifest.yaml").write_text(
            yaml.safe_dump(manifest, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        entry: dict = {
            "id": logical_id,
            "host_id": host_id,
            "schedule": item.get("schedule"),
            "log": item.get("log"),
        }

        if platform == "windows":
            run_ps = dest / "run.ps1"
            run_ps.write_text(RUN_PS1_TEMPLATE.format(venv=venv), encoding="utf-8")
            entry["run_ps"] = str(run_ps)
            entry["task_name"] = f"Overseer - {logical_id}"
            entry["task_match"] = item.get("task_match")
        else:
            run_sh = dest / "run.sh"
            run_sh.write_text(RUN_SH_TEMPLATE.format(venv=venv), encoding="utf-8")
            os.chmod(run_sh, 0o755)
            entry["run_sh"] = str(run_sh)
            entry["cron_match"] = item.get("cron_match")

        if args.register and agent.is_file():
            env = os.environ.copy()
            env.update(runner_env)
            subprocess.run(
                [
                    str(agent),
                    "manifest",
                    str(dest / "manifest.yaml"),
                    "--register-catalog",
                    "--catalog-only",
                    "--by",
                    "provision",
                ],
                env=env,
                check=False,
            )

        created.append(entry)

    catalog_json = {
        "platform": platform,
        "host_id": host_id,
        "catalog": str(catalog_path),
        "pipelines": created,
    }
    pathlib.Path(args.catalog_json_out).write_text(
        json.dumps(catalog_json, indent=2),
        encoding="utf-8",
    )
    print(f"Provisionados {len(created)} runners ({platform}) em {runners_root}")
    if host_id:
        print(f"host_id aplicado: {host_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
