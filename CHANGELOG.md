# Changelog

As alterações relevantes ao Overseer são registadas neste ficheiro.

## [Unreleased]

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
