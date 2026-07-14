from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

from overseer_agent import __version__
from overseer_sdk.client import OverseerClient, run_command
from overseer_sdk.manifest_runner import load_manifest, register_catalog, run_manifest


def get_api_url() -> str:
    return os.getenv("OVERSEER_API_URL", "http://127.0.0.1:8090").rstrip("/")


def get_api_token() -> str:
    return os.getenv("OVERSEER_API_TOKEN", "")


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    token = get_api_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _probe_api(api_url: str) -> bool:
    """Confirma que a API (e a sua DB) respondem a partir deste host/túnel."""
    try:
        with httpx.Client(timeout=10.0, trust_env=False) as client:
            res = client.get(f"{api_url}/v1/read/database", headers=_headers())
            return res.status_code == 200
    except httpx.HTTPError:
        return False


def _load_payload_file(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except OSError as exc:
        raise ValueError(f"payload-file inacessível: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"payload-file JSON inválido: linha {exc.lineno}") from exc
    if not isinstance(payload, dict):
        raise ValueError("payload-file deve conter um objeto JSON")
    return payload


def cmd_heartbeat(args: argparse.Namespace) -> int:
    api_url = get_api_url()
    client = OverseerClient(api_url=api_url, api_token=get_api_token())
    api_reachable = _probe_api(api_url)
    try:
        payload = _load_payload_file(args.payload_file)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    payload.update({"agent_version": __version__, "api_reachable": api_reachable})
    data = client.heartbeat(
        source_type="agent",
        status="ok" if api_reachable else "degraded",
        payload=payload,
    )
    print(f"heartbeat ok: {data['heartbeat']['source_id']} (api_reachable={api_reachable})")
    return 0


def cmd_exec(args: argparse.Namespace) -> int:
    if not args.command:
        print("Comando em falta após --.")
        return 2
    return run_command(
        args.command,
        pipeline_id=args.pipeline,
        pipeline_name=args.name,
        requested_by=args.by,
        api_url=get_api_url(),
        api_token=get_api_token(),
        cwd=args.cwd,
    )


def cmd_trigger(args: argparse.Namespace) -> int:
    host_id = str(args.host_id or "").strip()
    if not host_id:
        print("host_id é obrigatório (--host-id).", file=sys.stderr)
        return 2
    payload = {
        "pipeline_id": args.pipeline,
        "host_id": host_id,
        "trigger_type": "run_now",
        "requested_by": args.by,
        "runner_host": args.runner,
        "payload": {},
    }
    api_url = get_api_url()
    with httpx.Client(timeout=30.0, trust_env=False) as client:
        res = client.post(f"{api_url}/v1/orchestrate/triggers", json=payload, headers=_headers())
        res.raise_for_status()
        print(res.json())
    return 0


def cmd_manifest(args: argparse.Namespace) -> int:
    manifest = load_manifest(args.path)
    host_id = str(manifest.metadata.get("host_id") or "")
    client = OverseerClient(api_url=get_api_url(), api_token=get_api_token(), host_id=host_id)
    if args.register_catalog:
        register_catalog(manifest, client)
        print(f"catálogo registado: {manifest.pipeline_id}")
    if args.catalog_only:
        return 0
    return run_manifest(manifest, client=client, requested_by=args.by)


def _strip_command_separator(command: list[str]) -> list[str]:
    return command[1:] if command and command[0] == "--" else command


def main() -> int:
    parser = argparse.ArgumentParser(prog="overseer-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    heartbeat = sub.add_parser("heartbeat", help="Regista heartbeat do agente.")
    heartbeat.add_argument("--payload-file", default=None, help="Objeto JSON local a juntar ao payload do heartbeat.")
    heartbeat.set_defaults(func=cmd_heartbeat)

    exec_cmd = sub.add_parser("exec", help="Executa um comando e regista run/logs na API.")
    exec_cmd.add_argument("--pipeline", required=True)
    exec_cmd.add_argument("--name", default=None)
    exec_cmd.add_argument("--by", default="agent")
    exec_cmd.add_argument("--cwd", default=None)
    exec_cmd.add_argument("command", nargs=argparse.REMAINDER)
    exec_cmd.set_defaults(func=cmd_exec)

    trigger = sub.add_parser("trigger", help="Enfileira trigger run_now.")
    trigger.add_argument("pipeline")
    trigger.add_argument("--host-id", required=True, help="Identificador do host do deployment")
    trigger.add_argument("--by", default="agent")
    trigger.add_argument("--runner", default="any")
    trigger.set_defaults(func=cmd_trigger)

    manifest = sub.add_parser("manifest", help="Corre um pipeline a partir de um manifest YAML.")
    manifest.add_argument("path")
    manifest.add_argument("--register-catalog", action="store_true", help="Regista o DAG antes de correr.")
    manifest.add_argument("--catalog-only", action="store_true", help="Só regista o DAG, sem executar passos.")
    manifest.add_argument("--by", default="cron")
    manifest.set_defaults(func=cmd_manifest)

    args = parser.parse_args()
    if hasattr(args, "command"):
        args.command = _strip_command_separator(args.command)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
