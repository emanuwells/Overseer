# Scripts operacionais

Scripts suportados pelo repositório Overseer. Preferir os comandos documentados em [`COMMANDS.md`](../COMMANDS.md).

## Arranque e ambiente

| Script | Uso |
|---|---|
| `overseer-up.sh` / `overseer-up.ps1` / `overseer-up.cmd` | Arranque Docker local |
| `dev-ui.ps1` | UI local com Docker + browser opcional |
| `dev-frontend.ps1` | Vite dev server (hot-reload) |
| `ensure-env.sh` / `ensure-env.ps1` | Cria ou migra `secrets/.env` |

## Deploy

| Script | Uso |
|---|---|
| `deploy-prod.sh` / `deploy-prod.ps1` | Pull, rebuild Docker prod, nginx |
| `deploy-nginx-frontend.sh` | Publica SPA em `/Overseer/` |
| `install-nginx-overseer.sh` | Snippet nginx no host |
| `generate-frontend-config.sh` / `.ps1` | Injeta token em `overseer-config.js` |

## Base de dados e telemetria

| Script | Uso |
|---|---|
| `overseer_retention.py` | Retenção manual (30d por defeito) |
| `drop_legacy_tables.py` | Remove tabelas pré-`overseer_*` |
| `purge_legacy_pipelines.py` | Purga pipelines de teste/sonda |
| `purge_pipeline_data.py` | Purga telemetria de um pipeline |
| `audit_db_schema.py` | Auditoria read-only do schema |
| `scan_git_secrets.py` | Procura webhooks Slack no histórico Git |
| `maintenance/overseer_db_maintenance.py` | Runs presos, métricas CPU anómalas |
| `maintenance/reclassify_traffic_flow_partial_runs.py` | Corrige e restaura estados parciais Traffic Flow |
| `maintenance/purge_retention_telemetry.py` | Purga inicial de telemetria expirada com backup/restauro |
| `maintenance/deduplicate_ine_runs.py` | Consolida e restaura runs INE com dupla instrumentação |

## Integração e demonstração

| Script | Uso |
|---|---|
| `overseer_emit_demo.py` | Emite telemetria de exemplo para a API |
| `slack_daily_digest.py` | Digest Slack manual (cron opcional) |
| `slack_ops_test.py` | Smoke test Slack: `--digest`, `--failed`, `--resolved` |
| `provision-runners.sh` / `provision_runners.py` | Provisionamento de runners |
| `update-crontab-overseer.py` | Migra entradas crontab legadas |

## Windows / runners

Ver `scripts/windows/` para Task Scheduler, heartbeat, túnel SSH e onboarding de pipelines.

## Removidos (histórico)

Migrações one-shot (`migrate_host_id.sql`, `migrate_pipeline_host_suffix.py`, `assign_run_local_ids.py`) e o frontend HTML/JS estático foram retirados após migração para a SPA React e schema `overseer_*`.
