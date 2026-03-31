"""
Pequeno frontend/API para expor os logs de performance em JSON.

- Lê a tabela `logs` no servidor BAZE
- Pode exportar para ficheiro JSON (para ser servido estaticamente)
- Pode arrancar um endpoint HTTP simples (`/api/logs` e `/api/logs/<id>`)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import parse_qs, urlparse

from overseer_sdk.logger import get_logger
from overseer_monitor import OverseerLogRepository
from overseer_sdk.ssh_tunnel import SSHTunnelManager

DEFAULT_LIMIT = 50
LOGGER = get_logger("overseer_frontend")


def load_configs(config_dir: Path, secrets_dir: Path) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Carrega configurações necessárias para a ligação e monitorização."""
    db_config_path = secrets_dir / "database.json"
    if not db_config_path.exists():
        raise FileNotFoundError(f"Credenciais de BD não encontradas em {db_config_path}")

    db_config = json.loads(db_config_path.read_text(encoding="utf-8"))

    monitoring_defaults = {
        "logs_table": "Overseer.pipeline_runs",
        "script_name": "Microsoft_Forms_2_Datalake",
        "frontend_base_url": None,
    }

    monitoring_file = secrets_dir / "monitoring.json"
    if not monitoring_file.exists():
        alt_path = config_dir / "monitoring.json"
        monitoring_file = alt_path if alt_path.exists() else monitoring_file

    if monitoring_file.exists():
        loaded_monitoring = json.loads(monitoring_file.read_text(encoding="utf-8"))
        monitoring_defaults.update(loaded_monitoring)
    else:
        LOGGER.info("monitoring.json não encontrado; a usar defaults.")

    return db_config, monitoring_defaults


def create_repo(
    db_config: Dict[str, Any],
    monitoring_config: Dict[str, Any],
    secrets_dir: Path,
    use_ssh: bool = True,
) -> Tuple[OverseerLogRepository, SSHTunnelManager | None]:
    """Abre repositório de logs, iniciando túnel SSH se necessário."""
    ssh_config = db_config.get("ssh")
    db_cfg = db_config["database"]
    tunnel = None
    host = db_cfg.get("host", "localhost")
    port = db_cfg.get("port", 3306)

    if use_ssh and ssh_config:
        tunnel = SSHTunnelManager(
            ssh_host=ssh_config["host"],
            ssh_port=ssh_config["port"],
            ssh_user=ssh_config["user"],
            ssh_key_path=str(secrets_dir / ssh_config["key_filename"]),
            remote_bind_host=ssh_config.get("remote_bind_host", "localhost"),
            remote_bind_port=ssh_config.get("remote_bind_port", 3306),
        )
        tunnel.start()
        host = "localhost"
        port = tunnel.get_local_port()

    db_params = {
        "host": host,
        "port": port,
        "user": db_cfg["user"],
        "password": db_cfg["password"],
        "database": db_cfg["database"],
    }

    repo = OverseerLogRepository(
        db_params=db_params,
        table_name=monitoring_config.get("logs_table", "Overseer.pipeline_runs"),
    )
    return repo, tunnel


def build_payload(repo: OverseerLogRepository, monitoring_config: Dict[str, Any], limit: int) -> Dict[str, Any]:
    """Monta o JSON a ser consumido pelo frontend."""
    logs = repo.fetch_logs(limit=limit)
    return {
        "meta": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "script_name": monitoring_config.get("script_name"),
            "limit": limit,
            "frontend_base_url": monitoring_config.get("frontend_base_url"),
        },
        "data": logs,
    }


def serve(repo: OverseerLogRepository, monitoring_config: Dict[str, Any], host: str, port: int, default_limit: int) -> None:
    """Arranca um servidor HTTP muito simples apenas para JSON."""
    class LogsHandler(BaseHTTPRequestHandler):
        def _send_json(self, payload: Dict[str, Any], status: int = 200) -> None:
            body = json.dumps(payload, default=str, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            LOGGER.info("%s - %s", self.address_string(), format % args)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/api/logs"):
                query = parse_qs(parsed.query)
                limit = int(query.get("limit", [default_limit])[0])
                payload = build_payload(repo, monitoring_config, limit=limit)
                self._send_json(payload)
                return

            if parsed.path.startswith("/api/logs/"):
                try:
                    log_id = int(parsed.path.rsplit("/", 1)[-1])
                except ValueError:
                    self._send_json({"error": "Identificador inválido"}, status=400)
                    return

                log_item = repo.fetch_log(log_id)
                if not log_item:
                    self._send_json({"error": "Log não encontrado"}, status=404)
                    return
                self._send_json({"data": log_item})
                return

            self._send_json({"error": "Rota não encontrada"}, status=404)

    server = HTTPServer((host, port), LogsHandler)
    LOGGER.info("Servidor de logs ativo em http://%s:%s/api/logs", host, port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("Servidor interrompido pelo utilizador.")
    finally:
        server.server_close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Expose overseer logs as JSON")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Número de registos a devolver")
    parser.add_argument("--output", type=Path, help="Ficheiro para gravar o JSON (stdout se omitido)")
    parser.add_argument("--serve", action="store_true", help="Arranca mini-servidor HTTP (/api/logs)")
    parser.add_argument("--host", default="0.0.0.0", help="Host do servidor HTTP")
    parser.add_argument("--port", type=int, default=8050, help="Porta do servidor HTTP")
    parser.add_argument("--no-ssh", action="store_true", help="Ignora configuração de túnel SSH")
    parser.add_argument("--config-dir", type=Path, default=Path("config"), help="Diretório de config")
    parser.add_argument("--secrets-dir", type=Path, default=Path("secrets"), help="Diretório de secrets")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_config, monitoring_config = load_configs(args.config_dir, args.secrets_dir)
    repo = None
    tunnel = None

    try:
        repo, tunnel = create_repo(
            db_config=db_config,
            monitoring_config=monitoring_config,
            secrets_dir=args.secrets_dir,
            use_ssh=not args.no_ssh,
        )

        if args.serve:
            serve(repo, monitoring_config, host=args.host, port=args.port, default_limit=args.limit)
            return

        with repo:
            payload = build_payload(repo, monitoring_config, limit=args.limit)

        output_text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
        if args.output:
            args.output.write_text(output_text, encoding="utf-8")
            LOGGER.info("JSON de logs gravado em %s", args.output)
        else:
            print(output_text)
    finally:
        if repo:
            try:
                repo.__exit__(None, None, None)
            except Exception:
                pass
        if tunnel:
            tunnel.stop()


if __name__ == "__main__":
    main()




