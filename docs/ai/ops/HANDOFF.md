# Handoff — preparação para publicação pública

## Estado

- Configuração real de runners externalizada por `OVERSEER_RUNNERS_DIR`.
- Catálogos privados preservados fora da árvore rastreada.
- Documentação, testes e exemplos anonimizados.
- `AGENTS.md` alinhado ao template Repo v3.2.4; `README.md` e `PROJECT_CONTEXT.md` reescritos.
- Frontend SPA React (Vite) com base path configurável: `/ui/` (Docker/FastAPI) e `/Overseer/` (nginx).
- Scripts locais: `scripts/dev-ui.ps1` (stack Docker + UI com dados) e `scripts/dev-frontend.ps1` (Vite + API local ou túnel prod).
- Configuração em `secrets/.env` (migra automaticamente a partir de `.env` legado na raiz).
- Deploy produção: `scripts/deploy-prod.ps1` (requer `OVERSEER_SSH_TARGET`, `OVERSEER_REPO_PATH` e chave SSH).
- Alteração da visibilidade GitHub pendente numa sessão autenticada.

## Validação (5.8.29)

- Testes Python: 99 passaram.
- `secrets/.env` + `docker compose --env-file secrets/.env` validados localmente.
- UI local: `http://127.0.0.1:8090/ui/operations`; produção nginx: `/Overseer/`.

## Rollback

Restaurar o checkout, `secrets/.env`, catálogos, runtime e imagem registados no snapshot pré-migração. Não remover volumes.

