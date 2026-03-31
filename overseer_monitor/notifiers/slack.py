from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import requests
from requests import RequestException


class SlackNotifier:
    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str | Path] = None):
        self.webhook_url: Optional[str] = None
        self.channel: Optional[str] = None
        self.notify_on_ok: bool = False
        self.notify_on_warning: bool = True
        if config:
            self.webhook_url = config.get("webhook_url")
            self.channel = config.get("channel")
            self.notify_on_ok = bool(config.get("notify_on_ok", False))
            self.notify_on_warning = bool(config.get("notify_on_warning", True))
        elif config_path:
            self._load_from_path(Path(config_path))

    @property
    def enabled(self) -> bool:
        return bool(self.webhook_url)

    def _load_from_path(self, path: Path) -> None:
        if not path.exists():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
        self.webhook_url = data.get("webhook_url")
        self.channel = data.get("channel")
        self.notify_on_ok = bool(data.get("notify_on_ok", False))
        self.notify_on_warning = bool(data.get("notify_on_warning", True))

    def send(self, text: str) -> bool:
        if not self.enabled:
            return False
        payload: Dict[str, Any] = {"text": text}
        if self.channel:
            payload["channel"] = self.channel
        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            return resp.status_code < 400
        except RequestException:
            return False

    def notify_run(
        self,
        *,
        status: str,
        run_id: Optional[int],
        run_url: Optional[str],
        script_name: str,
        duration_seconds: Optional[float],
        error: Optional[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        status_upper = str(status).upper()
        if status_upper == "OK":
            emoji = ":white_check_mark:"
        elif status_upper == "WARNING":
            emoji = ":warning:"
        else:
            emoji = ":x:"
        lines = [
            f"{emoji} {script_name}",
            f"Estado: {status_upper}",
        ]
        if status_upper == "WARNING":
            warning_modules = (context or {}).get("warning_modules")
            if warning_modules:
                lines.append(f"Modulos com falha (nao-criticos): {', '.join(str(m) for m in warning_modules)}")
        if duration_seconds is not None:
            lines.append(f"Duracao: {duration_seconds:.2f}s")
        if run_id:
            lines.append(f"Run ID: {run_id}")
        if run_url:
            lines.append(f"Frontend: {run_url}")
        if context:
            # Exclude large fields from Slack context
            ctx_clean = {k: v for k, v in context.items() if k not in ("log_message", "warning_modules") and v is not None}
            if ctx_clean:
                lines.append(f"Contexto: {json.dumps(ctx_clean, ensure_ascii=False)}")
        if error:
            trimmed = (error[:280] + "...") if len(error) > 280 else error
            lines.append(f"Erro: {trimmed}")
        return self.send("\n".join(lines))
