# Trabalho

## Template, UI React e alinhamento — 2026-07-14

- [x] Sincronizar `AGENTS.md` e lacunas do template (`docs/resources/templates/`).
- [x] Reescrever README e PROJECT_CONTEXT ao novo contrato.
- [x] Migrar frontend para Vite + React + TypeScript com navegação SPA.
- [x] Corrigir base `/ui/` vs `/Overseer/` e scripts dev-ui / dev-frontend.
- [x] Publicar commit e push.
- [ ] Deploy produção: definir `OVERSEER_SSH_TARGET` e `OVERSEER_REPO_PATH`, depois `.\scripts\deploy-prod.ps1`.

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
- [ ] Alterar a visibilidade para pública numa sessão GitHub autenticada.
