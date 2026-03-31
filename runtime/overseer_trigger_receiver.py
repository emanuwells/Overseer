#!/usr/bin/env python3
"""Overseer Trigger Receiver — tiny HTTP server deployed on the nginx server.

Accepts POST /trigger with JSON body, writes to triggers/ directory.
The scheduler daemon on HP-Z2-EF polls this directory via SSH/SFTP.

Usage:
    python3 overseer_trigger_receiver.py          # default port 9099
    TRIGGER_PORT=8099 python3 overseer_trigger_receiver.py

Runs as systemd user service:
    systemctl --user start overseer-trigger
    systemctl --user enable overseer-trigger
"""
import json
import os
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler

TRIGGER_DIR = os.environ.get(
    "TRIGGER_DIR",
    "/usr/share/nginx/html/MAIATRON/apps/overseer/triggers",
)
PORT = int(os.environ.get("TRIGGER_PORT", 9099))
LOG_FILE = os.environ.get("TRIGGER_LOG", "/tmp/overseer_trigger_receiver.log")


def _log(msg: str) -> None:
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
    except Exception:
        pass


class TriggerHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler for trigger files."""

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        """Health check / list pending triggers."""
        try:
            files = sorted(os.listdir(TRIGGER_DIR)) if os.path.isdir(TRIGGER_DIR) else []
        except Exception:
            files = []
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "alive", "pending": len(files), "files": files}).encode())

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)

            filename = f"trigger-{int(time.time())}-{uuid.uuid4().hex[:8]}.json"
            filepath = os.path.join(TRIGGER_DIR, filename)

            os.makedirs(TRIGGER_DIR, exist_ok=True)
            tmp = filepath + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, filepath)

            _log(f"OK {filename} pipeline={data.get('pipeline_id','?')}")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "file": filename}).encode())
        except Exception as e:
            _log(f"ERR {e}")
            self.send_response(500)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())

    def log_message(self, format, *args):
        _log(" ".join(str(a) for a in args))


if __name__ == "__main__":
    os.makedirs(TRIGGER_DIR, exist_ok=True)
    httpd = HTTPServer(("0.0.0.0", PORT), TriggerHandler)
    _log(f"START port={PORT} dir={TRIGGER_DIR}")
    print(f"[overseer-trigger] Listening on 0.0.0.0:{PORT}  dir={TRIGGER_DIR}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        _log("STOP (keyboard)")
        print("\n[overseer-trigger] Stopped.")
