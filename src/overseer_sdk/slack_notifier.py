"""
Integração com Slack via Incoming Webhooks — módulo partilhado.

Suporta dois modos:
- Ficheiro JSON com ``webhook_url`` e ``channel`` opcionais
- Configuração por dicionário directamente

Utilização::

    from overseer_sdk.slack_notifier import SlackNotifier

    notifier = SlackNotifier(config_path=Path("secrets/slack.json"))
    notifier.send_message("Olá, mundo!")
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from requests import RequestException


logger = logging.getLogger("overseer_sdk.slack")


class SlackNotifier:
    """Encapsula o envio de mensagens para um canal Slack via webhook."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.webhook_url: Optional[str] = None
        self.channel: Optional[str] = None

        if config is not None:
            self._apply_config(config)
        elif config_path is not None:
            self._load_config(config_path)

    @property
    def is_enabled(self) -> bool:
        return bool(self.webhook_url)

    # ------------------------------------------------------------------
    # Config loaders
    # ------------------------------------------------------------------

    def _apply_config(self, data: Dict[str, Any]) -> None:
        self.webhook_url = data.get("webhook_url")
        self.channel = data.get("channel")
        if not self.webhook_url:
            logger.warning("Configuração Slack sem 'webhook_url'. Notificações desativadas.")

    def _load_config(self, config_path: Path) -> None:
        if not config_path.exists():
            logger.info(
                "Configuração Slack não encontrada em %s. Notificações desativadas.",
                config_path,
            )
            return
        try:
            with open(config_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except Exception as exc:
            logger.error("Não foi possível ler %s: %s", config_path, exc)
            return
        self._apply_config(data)

    # ------------------------------------------------------------------
    # Envio
    # ------------------------------------------------------------------

    def send_message(
        self,
        text: str,
        blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Envia uma mensagem simples para o webhook configurado."""
        if not self.is_enabled:
            return False

        payload: Dict[str, Any] = {"text": text}
        if self.channel:
            payload["channel"] = self.channel
        if blocks:
            payload["blocks"] = blocks

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            if response.status_code >= 400:
                logger.error(
                    "Falha ao enviar notificação Slack (%s): %s",
                    response.status_code, response.text,
                )
                return False
            return True
        except RequestException as exc:
            logger.error("Erro de rede ao enviar notificação Slack: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Notificação de run (genérica)
    # ------------------------------------------------------------------

    def notify_run(
        self,
        *,
        pipeline_name: str,
        status: str,
        stats: Dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        run_id: Optional[str] = None,
        run_url: Optional[str] = None,
        error_message: Optional[str] = None,
        error_events: Optional[List[Dict[str, Any]]] = None,
        hostname: Optional[str] = None,
        extra_lines: Optional[List[str]] = None,
    ) -> None:
        """
        Gera e envia uma mensagem com o resumo de execução de qualquer pipeline.

        Os campos de ``stats`` são genéricos — cada pipeline passa o que tiver.
        """
        if not self.is_enabled:
            return

        duration_seconds = (end_time - start_time).total_seconds()
        status_emoji = "✅" if status.lower() in {"success", "ok"} else "⚠️"
        title = f"{status_emoji} {pipeline_name}"

        lines: List[str] = [
            f"*Estado*: {status.upper()}",
            f"*Início*: {start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"*Fim*: {end_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"*Duração*: {duration_seconds:.1f}s",
        ]

        # Stats genéricos
        for key, value in stats.items():
            lines.append(f"*{key}*: {value}")

        if hostname:
            lines.append(f"*Hostname*: {hostname}")
        if run_url and run_id:
            lines.append(f"*Log run*: <{run_url}|{run_id}>")
        elif run_id:
            lines.append(f"*Log run*: {run_id}")
        if error_message:
            truncated = (error_message[:180] + ".") if len(error_message) > 180 else error_message
            lines.append(f"*Erro*: {truncated}")

        events = error_events or []
        if events:
            lines.append("*Detalhe de erros (máx. 5)*:")
            for event in events[:5]:
                cat = event.get("category", "erro")
                ctx = event.get("context", "")
                msg = event.get("message", "")
                msg_short = (msg[:140] + "...") if len(msg) > 140 else msg
                lines.append(f"- {cat}: {ctx} -> {msg_short}")
            if len(events) > 5:
                lines.append(f"- ... e mais {len(events) - 5} erros.")

        if extra_lines:
            lines.extend(extra_lines)

        text = f"{title}\n" + "\n".join(lines)
        self.send_message(text)
