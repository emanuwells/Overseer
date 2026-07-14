# Handoff — preparação para publicação pública

## Estado

- Configuração real de runners externalizada por `OVERSEER_RUNNERS_DIR`.
- Catálogos privados preservados fora da árvore rastreada.
- Documentação, testes e exemplos anonimizados.
- `AGENTS.md` alinhado ao template Repo v3.2.4; `README.md` e `PROJECT_CONTEXT.md` reescritos.
- Frontend migrado para SPA React (Vite) com build integrado no Docker.
- Produção migrada anteriormente; API, base de dados e dashboard validados.
- Deploy produção desta release: executar `git pull`, `docker compose ... up --build -d` e `scripts/deploy-nginx-frontend.sh` no servidor após push.
- Alteração da visibilidade GitHub pendente numa sessão autenticada.

## Validação (5.8.27)

- Testes Python: 99 passaram.
- Build frontend: `npm run build` (validado em diretório temporário local; `node_modules` no Google Drive falha com EPERM).
- Build Docker: concluído com stage Node + `frontend/dist`.
- Redirects `/` e `/ui` → `/ui/` confirmados em testes.

## Rollback

Restaurar o checkout, `.env`, catálogos, runtime e imagem registados no snapshot pré-migração. Não remover volumes.

