"""
Validador de dados partilhado — funcionalidades base reutilizáveis.

Validações específicas de cada pipeline devem estender ou compor
com esta classe.

Utilização::

    from overseer_sdk.validator import DataValidator

    v = DataValidator()
    ok, erros = v.validate_indicator({"id": "X", "url_table": "https://..."})
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


logger = logging.getLogger("overseer_sdk.validator")


class DataValidator:
    """Validador genérico reutilizável por qualquer pipeline."""

    # ------------------------------------------------------------------
    # Indicadores
    # ------------------------------------------------------------------

    def validate_indicator(self, indicator: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida um indicador scraped.

        Returns:
            (é_válido, lista_de_erros)
        """
        errors: List[str] = []

        indicator_id = indicator.get("id")
        if not indicator_id or not str(indicator_id).strip():
            errors.append("indicator_id vazio ou ausente")

        url_table = indicator.get("url_table")
        if not url_table or not str(url_table).strip():
            errors.append("url_table vazio ou ausente")
        elif not self._is_valid_url(str(url_table)):
            errors.append(f"url_table inválido: {url_table}")

        return len(errors) == 0, errors

    # ------------------------------------------------------------------
    # Payloads
    # ------------------------------------------------------------------

    def validate_payload(self, payload: Any) -> Tuple[bool, List[str]]:
        """Valida um payload individual (dict não-vazio)."""
        errors: List[str] = []
        if payload is None:
            errors.append("payload é None")
            return False, errors
        if not isinstance(payload, dict):
            errors.append(f"payload não é dict: {type(payload).__name__}")
            return False, errors
        if not payload:
            errors.append("payload é dict vazio")
        return len(errors) == 0, errors

    # ------------------------------------------------------------------
    # URLs
    # ------------------------------------------------------------------

    def validate_source_url(self, url: Optional[str]) -> Tuple[bool, List[str]]:
        """Valida uma URL de fonte de dados."""
        errors: List[str] = []
        if not url:
            errors.append("URL ausente")
            return False, errors
        if not self._is_valid_url(url):
            errors.append(f"URL inválida: {url}")
        return len(errors) == 0, errors

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        pattern = re.compile(
            r"^https?://"
            r"[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=%\-]+"
        )
        return bool(pattern.match(url.strip()))

    @staticmethod
    def is_local_or_test_url(url: str) -> bool:
        """Verifica se URL é local/teste."""
        parsed = urlparse(str(url or "").strip())
        if parsed.scheme.lower() == "file":
            return True
        host = (parsed.hostname or "").strip().lower()
        if not host:
            return True
        local_aliases = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
        if host in local_aliases or host.startswith("127."):
            return True
        if host in {"example.com", "example.org", "example.net"}:
            return True
        if host.endswith((".example", ".invalid", ".test")):
            return True
        return False
