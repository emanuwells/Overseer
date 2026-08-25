# Changelog

As alterações relevantes ao Overseer são registadas neste ficheiro.

## [Unreleased]

### Changed

- Automação GitHub alinhada com o WELLS 1.3.0: CI para backend, frontend e Docker, mais Dependabot para Actions, npm, pip e Docker.
- A contagem dos três avisos Slack ignora notificações legadas sem número, permitindo regularizar episódios de falha já em curso.
- Toolkit WELLS local sincronizado com a versão **1.3.0** (`.agents/`, fora do Git); `PROJECT_CONTEXT.md` atualizado para refletir a versão efetiva do runtime.
- Alertas Slack de falha limitados a três avisos imediatos por episódio e deployment; o terceiro anuncia a passagem para o digest diário até resolução.
- Dependências frontend corrigidas para versões sem os avisos de segurança detetados: `react-router-dom`/`react-router` 7.18.2, `nanoid` 3.3.18 e `postcss` 8.5.26.

## [5.8.37] - 2026-07-26

### Changed

- Toolkit WELLS local actualizado para **0.5.0** (`.agents/`, fora do Git); `PROJECT_CONTEXT.md` regista a versão e o routing via `INDEX.md`.

## [5.8.36] - 2026-07-25

### Changed

- README alinhado ao template WELLS: Tecnologias, Troubleshooting, Segurança, Contribuição, Licença e Changelog.
- `PROJECT_CONTEXT.md`: removida decisão obsoleta sobre visibilidade pública do GitHub.

## [5.8.35] - 2026-07-25

### Added

- `CONTRIBUTING.md` e `SECURITY.md` na raiz, alinhados à estrutura WELLS.

### Removed

- `AGENTS.md`, `docs/ai/` e `tasks/` do núcleo versionado (migrados para toolkit local `.agents/`, ignorado pelo Git).

### Changed

- README, `PROJECT_CONTEXT.md`, `COMMANDS.md` e docs de governação/arquitetura sem referências quebradas a `docs/ai` ou `AGENTS.md` na raiz.

## [5.8.34] - 2026-07-14

### Added

- `docs/resources/templates/.env.example` — template de configuração (corrigido `.gitignore` que bloqueava `docs/resources/templates/`).
- `scripts/README.md` — índice dos scripts suportados.

### Removed

- Migrações one-shot obsoletas: `migrate_host_id.sql`, `migrate_pipeline_host_suffix.py`, `maintenance/assign_run_local_ids.py` (backfill integrado em `init_schema()`).

### Changed

- README, `database.md`, `deployment.md`, ADR 0001 e SECURITY alinhados com repo público e SPA React.
- Badge de versão e variáveis de retenção documentadas no README.

## [5.8.33] - 2026-07-14

### Added

- `scripts/drop_legacy_tables.py` — remove tabelas pré-`overseer_*` (orchestrator local, `pipeline_*`, medidata, alertas antigos).
- Constantes `LEGACY_DROP_TABLES`, `GOVERNANCE_TABLES` e `CANONICAL_TABLES` em `store.py`.

### Changed

- `audit_db_schema.py` reporta dry-run de drop de tabelas legado.
- Tabelas de governação SSO/RBAC (`overseer_identity_*`, `overseer_permission_*`) mantêm-se.

## [5.8.32] - 2026-07-14

### Security

- Exemplos e testes deixam de usar URLs `hooks.slack.com` (evita alertas GitGuardian em placeholders).

### Added

- Retenção automática de telemetria (30 dias por defeito, `OVERSEER_RETENTION_AUTO`, `OVERSEER_RETENTION_DAYS`).
- `telemetry_since` / `first_run_label` no summary calculados a partir do `MIN(started_at)` na base de dados.

### Changed

- API aplica purge de retenção no arranque (throttle diário via marcador em `runtime/`).
- Ops Center (MAIATRON-HUB) passa a receber contagens e data «desde» coerentes com a API.

## [5.8.31] - 2026-07-14

### Added

- Camada canónica de nomes de pipeline (`pipeline_names.py`): catálogo + remoção de prefixos (`OVERSEER_NAME_PREFIX_STRIP`, default `Yunex `).
- Componentes UI: `Modal`, `Drawer`, `DeploymentPicker`, `PipelineInspector`, `RunDetailPanel`.
- Testes de regressão Slack e unitários para nomes normalizados.

### Changed

- API (`store`), Slack (digest/alertas) e frontend (`pipelineLabel`) usam a mesma regra de nome canónico.
- Operações: drawer com inspector; modal para detalhe de run; KPI «Falhas» filtra a tabela.
- Runs: detalhe em painel (desktop) ou modal (mobile); breadcrumbs com deployment.
- DAG: `DeploymentPicker` no header; drawer ao clicar num nó.
- `AppShell`: breadcrumbs clicáveis e atalhos Operações/Runs/DAG por deployment.
- README: diagrama genérico de integração pipeline externo → API (remove referências inexistentes).

## [5.8.30] - 2026-07-14

### Fixed

- Nginx SPA em `/Overseer/`: `root` + `try_files` em vez de `alias` (deep links como `/Overseer/operations`).
- `deploy-nginx-frontend.sh` remove fallbacks legados por rota; usar `install-nginx-overseer.sh` no servidor.

## [5.8.29] - 2026-07-14

### Added

- `scripts/ensure-env.ps1` / `ensure-env.sh` — cria ou migra configuração para `secrets/.env`.

### Changed

- Configuração local e produção passa de `.env` na raiz para **`secrets/.env`**; Compose usa `--env-file secrets/.env`.
- README com diagrama Mermaid da **arquitetura técnica do pipeline** (separado da camada Overseer).
- Deploy remoto actualizado para `secrets/.env` e publicação nginx em `/Overseer/`.
- OpenAPI e documentação de integração apontam para `/ui/operations` em vez de HTML legado.

## [5.8.28] - 2026-07-14

### Added

- Builds separados: `npm run build` (`/ui/`) e `npm run build:nginx` (`/Overseer/`).
- `scripts/dev-ui.ps1` — Docker local com UI e dados.
- `scripts/dev-frontend.ps1` — Vite com API local ou túnel SSH para prod.
- `scripts/deploy-prod.ps1` / `deploy-prod.sh` — alinhamento git + Docker + nginx.
- `docker/entrypoint.sh` — injecta `overseer-config.js` a partir de `OVERSEER_API_TOKEN`.

### Changed

- `deploy/nginx/overseer-locations.conf` inclui SPA em `/Overseer/`.
- `deploy-nginx-frontend.sh` usa `build:nginx` e publica `dist-nginx/`.
- Vite base path configurável via `.env.production` / `.env.nginx`.

## [5.8.27] - 2026-07-14

### Added

- Pasta `docs/resources/templates/` com `.env.example`, templates de documentação e `.gitignore.template`.
- Frontend React (Vite, TypeScript, React Router, TanStack Query, Tailwind) com navegação SPA profissional.
- Build multi-stage Node no Dockerfile para `frontend/dist/`.

### Changed

- `AGENTS.md` alinhado ao template Repo v3.2.4 com extensão Overseer para pastas de produto.
- Reescritos `README.md` e `PROJECT_CONTEXT.md` ao novo contrato normativo.
- `docs/ai/ops/RUNBOOK.md` actualizado para MariaDB e `/v1/health`.
- Redirects da API e nginx actualizados para SPA em `/ui/` e `/Overseer/`.
- `scripts/deploy-nginx-frontend.sh` publica `frontend/dist/`.

### Removed

- Páginas HTML estáticas e `frontend/js/app.js` substituídos pela SPA React.

## [5.8.26] - 2026-07-14

### Changed

- Preparado o repositório para consulta pública sob licença proprietária.
- Externalizada a configuração real de runners através de `OVERSEER_RUNNERS_DIR`.
- Externalizado o estado de runtime através de `OVERSEER_RUNTIME_DIR`.
- Substituída documentação específica de ambientes privados por instruções agnósticas.
- Simplificada a governação do repositório e removidos templates e adaptadores redundantes.

### Security

- Removidos da árvore pública hosts, endereços, utilizadores, caminhos e catálogos operacionais reais.
