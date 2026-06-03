from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from overseer_agent import __version__
from src.overseer_core.runners import register_runner

DEFAULT_API = os.getenv("OVERSEER_API_URL", "http://127.0.0.1:8090").rstrip("/")
TOKEN = os.getenv("OVERSEER_API_TOKEN", "")


def _headers() -> dict[str, str]:
    h = {"Accept": "application/json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


def cmd_heartbeat(_: argparse.Namespace) -> int:
    row = register_runner(agent_version=__version__)
    if not DEFAULT_API:
        print(row)
        return 0
    try:
        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                f"{DEFAULT_API}/v1/runners/heartbeat",
                json={"hostname": row["hostname"], "agent_version": __version__},
                headers=_headers(),
            )
            res.raise_for_status()
        print(f"heartbeat ok: {row['hostname']}")
    except Exception as exc:
        print(f"heartbeat local only (API unreachable): {exc}")
        print(row)
    return 0


def cmd_consume(args: argparse.Namespace) -> int:
    orch = ROOT / "orchestrator.py"
    runner = args.runner or ""
    cmd = [sys.executable, str(orch), "trigger", "consume", "--max", str(args.max)]
    if runner:
        cmd.extend(["--runner", runner])
    return subprocess.run(cmd, cwd=str(ROOT), check=False).returncode


def main() -> int:
    parser = argparse.ArgumentParser(prog="overseer-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    hb = sub.add_parser("heartbeat", help="Register runner heartbeat")
    hb.set_defaults(func=cmd_heartbeat)

    consume = sub.add_parser("consume-triggers", help="Consume DB triggers via orchestrator")
    consume.add_argument("--runner", default="")
    consume.add_argument("--max", type=int, default=20)
    consume.set_defaults(func=cmd_consume)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
