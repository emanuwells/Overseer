# Changelog

As alterações relevantes ao Overseer são registadas neste ficheiro.

## [Unreleased]

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
