"""
Scraper do Webapp Medidata.
Estrutura análoga ao microsoft_forms_2_datalake/src/forms_reader.py.

Faz scraping dos indicadores do Medidata, parseia HTML tables e JSON endpoints.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from overseer_sdk.logger import get_logger

DEFAULT_BASE_URL = "http://webapp.cm-maia.local/medidata/"
DEFAULT_LIST_URL = urljoin(DEFAULT_BASE_URL, "listagem.aspx")
DEFAULT_TIMEOUT_SECONDS = 30

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}

TIME_COLUMNS = (
    "DATA",
    "Data_Referencia",
    "ano_aberto",
    "DATA_RECEP_PROV",
    "data",
    "DataEvento",
    "data_evento",
    "tstamp",
)


class MedidataScraper:
    """
    Leitor/scraper dos indicadores do Webapp Medidata.
    Análogo ao FormsReader do pipeline microsoft_forms_2_datalake.
    """

    def __init__(self, mappings: Dict[str, Any]):
        self.logger = get_logger("scraper")
        self.mappings = mappings  # series_config dict
        self.timeout = DEFAULT_TIMEOUT_SECONDS

    def set_timeout(self, timeout: int) -> None:
        self.timeout = timeout

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _get_response(self, url: str) -> requests.Response:
        response = requests.get(url, headers=HEADERS, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _get_soup(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = self._get_response(url)
            return BeautifulSoup(response.content, "html.parser")
        except Exception as exc:
            self.logger.error(f"Falha ao obter HTML de {url}: {exc}")
            return None

    def _get_raw_content(self, url: str) -> Optional[str]:
        try:
            response = self._get_response(url)
            return response.text
        except Exception as exc:
            self.logger.warning(f"Falha ao obter JSON raw de {url}: {exc}")
            return None

    # ------------------------------------------------------------------
    # Date/time helpers
    # ------------------------------------------------------------------

    @staticmethod
    def parse_date_value(date_str: Any) -> datetime:
        if not date_str:
            return datetime.min
        date_str = str(date_str).strip()
        json_date_match = re.search(r"/Date\((\d+)\)/", date_str)
        if json_date_match:
            try:
                timestamp = int(json_date_match.group(1)) / 1000
                return datetime.fromtimestamp(timestamp)
            except Exception:
                return datetime.min

        formats = ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%Y-%m-%d", "%Y")
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return datetime.min

    @staticmethod
    def infer_event_ts(payload: Dict[str, Any]) -> Optional[datetime]:
        """Infere timestamp de evento a partir de colunas conhecidas."""
        lowered = {str(k).lower(): k for k in payload.keys()}
        for candidate in TIME_COLUMNS:
            key = lowered.get(candidate.lower())
            if not key:
                continue
            parsed = MedidataScraper.parse_date_value(payload.get(key))
            if parsed > datetime.min:
                return parsed
        return None

    def _sort_data_by_time(
        self, data_list: List[Dict[str, Any]], columns: List[str]
    ) -> None:
        """Ordena dados pela coluna temporal detectada."""
        target_col = None
        lower_columns = [col.lower() for col in columns]
        for candidate in TIME_COLUMNS:
            if candidate.lower() in lower_columns:
                target_col = columns[lower_columns.index(candidate.lower())]
                break
        if target_col:
            data_list.sort(key=lambda row: self.parse_date_value(row.get(target_col)))

    # ------------------------------------------------------------------
    # Source discovery
    # ------------------------------------------------------------------

    def discover_sources(
        self,
        base_url: str,
        list_url: Optional[str] = None,
        list_file: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Faz GET a listagem.aspx (ou ficheiro local), parseia HTML table,
        retorna lista de indicadores com {id, area, title, application, url_table, url_json}.
        """
        if not list_url:
            list_url = urljoin(base_url, "listagem.aspx")

        soup = self._load_list_soup(list_url, list_file)
        if not soup:
            raise RuntimeError("Falha ao carregar a listagem principal.")

        main_table = soup.find("table")
        if not main_table:
            raise RuntimeError("Tabela principal não encontrada em listagem.")

        rows = main_table.find_all("tr")
        self.logger.info(f"Rows encontrados na listagem: {len(rows)}")

        entries: List[Dict[str, Any]] = []
        for tr in rows[1:]:
            cols = tr.find_all("td")
            if len(cols) < 5:
                continue

            area = cols[0].get_text(strip=True)
            indicator_name = cols[1].get_text(strip=True)
            application = cols[2].get_text(strip=True)

            link_table = cols[3].find("a")
            url_table = (
                link_table["href"] if link_table and link_table.has_attr("href") else None
            )
            link_json = cols[4].find("a")
            url_json = (
                link_json["href"] if link_json and link_json.has_attr("href") else None
            )
            if not url_table:
                continue

            full_url_table = urljoin(base_url, url_table)
            full_url_json = urljoin(base_url, url_json) if url_json else None
            item_id = Path(full_url_table).name.replace(".aspx", "")

            entries.append(
                {
                    "id": item_id,
                    "area": area,
                    "title": indicator_name,
                    "application": application,
                    "url_table": full_url_table,
                    "url_json": full_url_json,
                }
            )

        self.logger.info(f"Indicadores descobertos: {len(entries)}")
        return entries

    def _load_list_soup(
        self, list_url: str, list_file: Optional[str]
    ) -> Optional[BeautifulSoup]:
        if list_file:
            list_path = Path(list_file)
            if not list_path.exists():
                self.logger.error(f"Ficheiro de listagem offline não encontrado: {list_path}")
                return None
            self.logger.info(f"A usar listagem offline: {list_path}")
            html = list_path.read_text(encoding="utf-8")
            return BeautifulSoup(html, "html.parser")
        self.logger.info(f"A obter listagem remota: {list_url}")
        return self._get_soup(list_url)

    # ------------------------------------------------------------------
    # Individual indicator scraping
    # ------------------------------------------------------------------

    def scrape_indicator(self, indicator: Dict[str, Any]) -> Dict[str, Any]:
        """
        Faz scrape de um indicador: HTML table + JSON endpoint.
        Retorna dict com {id, area, title, application, url_table, url_json, columns, data, json_data}.
        """
        indicator_id = str(indicator.get("id") or "")
        table_url = str(indicator.get("url_table") or "")
        json_url = indicator.get("url_json")
        has_issue = False

        self.logger.info(f"A processar [{indicator.get('area')}] {indicator.get('title')}")

        try:
            table_cols, table_data = self._scrape_table_page(table_url)
            if not table_cols and not table_data:
                has_issue = True
                self.logger.warning(
                    f"Tabela indisponível/vazia para indicador {indicator_id} ({table_url})."
                )
        except Exception as exc:
            has_issue = True
            table_cols, table_data = [], []
            self.logger.warning(f"Falha ao processar tabela {indicator_id}: {exc}")

        json_data: List[Dict[str, Any]] = []
        if isinstance(json_url, str) and json_url:
            try:
                json_blob = self._scrape_json_page(json_url)
                if json_blob is None:
                    has_issue = True
                    self.logger.warning(
                        f"JSON indisponível/inválido para indicador {indicator_id} ({json_url})."
                    )
                else:
                    json_data = json_blob
            except Exception as exc:
                has_issue = True
                self.logger.warning(f"Falha ao processar JSON {indicator_id}: {exc}")

        return {
            "id": indicator_id,
            "area": indicator.get("area"),
            "title": indicator.get("title"),
            "application": indicator.get("application"),
            "url_table": table_url,
            "url_json": json_url,
            "columns": table_cols,
            "data": table_data,
            "json_data": json_data,
            "has_issue": has_issue,
        }

    def scrape_all(
        self, indicators: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Itera todos os indicadores, faz scrape de cada um.
        Retorna (lista de resultados, total de warnings).
        """
        results: List[Dict[str, Any]] = []
        warning_count = 0

        for entry in indicators:
            result = self.scrape_indicator(entry)
            results.append(result)
            if result.get("has_issue"):
                warning_count += 1

        return results, warning_count

    def _scrape_table_page(
        self, url: str
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        soup = self._get_soup(url)
        if not soup:
            return [], []

        table = soup.find("table")
        if not table:
            return [], []

        headers: List[str] = []
        header_row = table.find("tr")
        if header_row:
            headers = [th.get_text(strip=True) for th in header_row.find_all("th")]

        rows_data: List[Dict[str, Any]] = []
        for tr in table.find_all("tr")[1:]:
            cols = tr.find_all("td")
            if not cols:
                continue
            row_dict: Dict[str, Any] = {}
            for index, col in enumerate(cols):
                if index >= len(headers):
                    continue
                key = headers[index]
                value: Any = col.get_text(strip=True)
                if key in {"TOTAL", "QTD_EXEC"} or "qtd" in key.lower():
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                row_dict[key] = value
            if row_dict:
                rows_data.append(row_dict)

        if rows_data:
            self._sort_data_by_time(rows_data, headers)

        return headers, rows_data

    def _scrape_json_page(self, url: str) -> Optional[List[Dict[str, Any]]]:
        content = self._get_raw_content(url)
        if not content:
            return None
        try:
            start = content.find("[")
            end = content.rfind("]")
            if start != -1 and end != -1:
                return json.loads(content[start : end + 1])
            loaded = json.loads(content)
            return loaded if isinstance(loaded, list) else None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Payload hashing
    # ------------------------------------------------------------------

    @staticmethod
    def compute_payload_hash(payload: Any) -> str:
        """Calcula SHA-256 hash canónico de um payload."""
        payload_dict = payload if isinstance(payload, dict) else {"value": payload}
        canonical = json.dumps(
            payload_dict, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def serialize_payload(payload: Any) -> str:
        """Serializa payload para JSON canónico."""
        payload_dict = payload if isinstance(payload, dict) else {"value": payload}
        return json.dumps(
            payload_dict, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

    # ------------------------------------------------------------------
    # Mapping precheck
    # ------------------------------------------------------------------

    def run_mapping_precheck(
        self, indicators: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Cross-referencia indicadores scraped vs mappings carregados.
        Retorna stats: {mapped, unmapped, orphan, warnings}.
        """
        mapping_ids: set = set()
        for key in self.mappings.keys():
            normalized = self._normalize_key(key)
            if normalized:
                mapping_ids.add(normalized)

        scraped_ids = {
            self._normalize_key(item.get("id"))
            for item in indicators
            if self._normalize_key(item.get("id"))
        }

        mapped = scraped_ids & mapping_ids
        unmapped = scraped_ids - mapping_ids
        orphan = mapping_ids - scraped_ids

        return {
            "mapped": len(mapped),
            "unmapped": len(unmapped),
            "orphan": len(orphan),
            "warnings": len(unmapped) + len(orphan),
        }

    @staticmethod
    def _normalize_key(raw_value: Any) -> str:
        value = str(raw_value or "").strip().lower()
        return re.sub(r"[^a-z0-9]+", "", value)
