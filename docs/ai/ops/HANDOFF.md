# Handoff — preparação para publicação pública

## Estado

- Configuração real de runners externalizada por `OVERSEER_RUNNERS_DIR`.
- Catálogos privados preservados fora da árvore rastreada.
- Documentação, testes e exemplos anonimizados.
- `AGENTS.md` alinhado ao template Repo v3.2.4; `README.md` e `PROJECT_CONTEXT.md` reescritos.
- Frontend SPA React (Vite) com base path configurável: `/ui/` (Docker/FastAPI) e `/Overseer/` (nginx).
- Scripts locais: `scripts/dev-ui.ps1` (stack Docker + UI com dados) e `scripts/dev-frontend.ps1` (Vite + API local ou túnel prod).
- Deploy produção: `scripts/deploy-prod.ps1` (requer `OVERSEER_SSH_TARGET`, `OVERSEER_REPO_PATH` e chave SSH).
- Alteração da visibilidade GitHub pendente numa sessão autenticada.

## Validação (5.8.28)

- Testes Python: 99 passaram.
- Build frontend: `npm run build` e `npm run build:nginx`.
- Build Docker: concluído; `overseer-config.js` injectado no arranque via `docker/entrypoint.sh`.
- UI local: `.\scripts\dev-ui.ps1` → `http://127.0.0.1:8090/ui/operations` com API e BD.

## Rollback

Restaurar o checkout, `.env`, catálogos, runtime e imagem registados no snapshot pré-migração. Não remover volumes.

