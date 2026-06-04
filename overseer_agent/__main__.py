from __future__ import annotations

import argparse
import os
import sys

import httpx

from overseer_agent import __version__
from overseer_sdk.client import OverseerClient, run_command

DEFAULT_API = os.getenv("OVERSEER_API_URL", "http://127.0.0.1:8090").rstrip("/")
TOKEN = os.getenv("OVERSEER_API_TOKEN", "")


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    return headers


def cmd_heartbeat(_: argparse.Namespace) -> int:
    client = OverseerClient(api_url=DEFAULT_API, api_token=TOKEN)
    data = client.heartbeat(source_type="agent", payload={"agent_version": __version__})
    print(f"heartbeat ok: {data['heartbeat']['source_id']}")
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
        api_url=DEFAULT_API,
        api_token=TOKEN,
        cwd=args.cwd,
    )


def cmd_trigger(args: argparse.Namespace) -> int:
    payload = {
        "pipeline_id": args.pipeline,
        "trigger_type": "run_now",
        "requested_by": args.by,
        "runner_host": args.runner,
        "payload": {},
    }
    with httpx.Client(timeout=30.0) as client:
        res = client.post(f"{DEFAULT_API}/v1/orchestrate/triggers", json=payload, headers=_headers())
        res.raise_for_status()
        print(res.json())
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    payload = {"requested_by": args.by, "background": not args.foreground}
    with httpx.Client(timeout=None) as client:
        res = client.post(
            f"{DEFAULT_API}/v1/orchestrate/pipelines/{args.pipeline}/run",
            json=payload,
            headers=_headers(),
        )
        res.raise_for_status()
        print(res.json())
    return 0


def _strip_command_separator(command: list[str]) -> list[str]:
    return command[1:] if command and command[0] == "--" else command


def main() -> int:
    parser = argparse.ArgumentParser(prog="overseer-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    heartbeat = sub.add_parser("heartbeat", help="Regista heartbeat do agente.")
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
    trigger.add_argument("--by", default="agent")
    trigger.add_argument("--runner", default="any")
    trigger.set_defaults(func=cmd_trigger)

    run = sub.add_parser("run", help="Pede execução de pipeline via API de orquestração.")
    run.add_argument("pipeline")
    run.add_argument("--by", default="agent")
    run.add_argument("--foreground", action="store_true")
    run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    if hasattr(args, "command"):
        args.command = _strip_command_separator(args.command)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
