# Trabalho

## Template, UI React e alinhamento — 2026-07-14

- [x] Sincronizar `AGENTS.md` e lacunas do template (`docs/resources/templates/`).
- [x] Reescrever README e PROJECT_CONTEXT ao novo contrato.
- [x] Migrar frontend para Vite + React + TypeScript com navegação SPA.
- [x] Corrigir base `/ui/` vs `/Overseer/` e scripts dev-ui / dev-frontend.
- [x] Publicar commit e push.
- [x] Deploy produção baze2 (`875dc83`, UI em `/Overseer/`, `secrets/.env`).

## Documentação e digest Slack — 2026-07-14

- [x] Reestruturar README e PROJECT_CONTEXT segundo o contrato do repositório.
- [x] Remover heartbeats e triggers em fila do digest Slack.
- [x] Evitar menções ao canal em digests sem situações acionáveis.
- [x] Acrescentar testes de regressão específicos.
- [x] Publicar e promover a alteração depois de autorização explícita.

## Publicação agnóstica — 2026-07-14

- [x] Criar backups verificáveis antes da migração.
- [x] Externalizar a configuração de runners.
- [x] Remover configuração operacional da árvore pública.
- [x] Simplificar documentação e governação.
- [x] Executar testes, validação Docker e auditoria de dados.
- [x] Publicar a história limpa e validar o GitHub.
- [x] Migrar produção e confirmar health.
- [x] Alterar a visibilidade para pública numa sessão GitHub autenticada.

## Harmonização nomes, UX e deploy — 2026-07-14

- [x] `pipeline_names.py` + normalização em store e Slack.
- [x] Testes unitários e regressão Slack para nomes canónicos.
- [x] Modal, Drawer, DeploymentPicker, refactor Operações/Runs/DAG.
- [x] README (diagrama genérico), CHANGELOG 5.8.31, `.env.example`.
- [x] Validar pytest + build frontend + deploy baze2 + smoke URLs.

## Limpeza repo público — 2026-07-14

- [x] Remover scripts de migração one-shot obsoletos.
- [x] Adicionar `docs/resources/templates/.env.example` e corrigir `.gitignore`.
- [x] Alinhar README, arquitetura, ADR, SECURITY e `scripts/README.md`.
- [x] Deploy produção e alinhar git.

## Contributors, Slack e Git — 2026-07-15

- [x] Backup + `git filter-repo` para remover `Co-authored-by: Cursor` + force push `main`.
- [x] Diagnosticar Slack em baze2: `secrets/slack.json` ausente; copiado e `webhook_configured=True`.
- [x] Enviar digest + alertas `[TEST]` (falha e resolução) em produção.
- [x] `scripts/slack_ops_test.py` + documentação (`COMMANDS.md`, `scripts/README.md`, `AGENTS.md`).
- [ ] Commit/push e alinhar SHA local/GitHub/baze2 após rebuild.

## Publicação agnóstica — 2026-07-14
