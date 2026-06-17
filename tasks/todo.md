# Todo

Estado operacional das iterações em curso.

## Iteração Atual

**Data:** 2026-06-17  
**Estado:** Em deploy  
**Risco:** Médio

### Objetivo

- Reescrever README do Overseer, corrigir documentação obsoleta, preparar Medidata_Pipeline e fazer deploy prod + WS1207.

### Feito

- [x] `README.md` reescrito como documentação do núcleo Overseer.
- [x] `.env.example` alinhado com variáveis `OVERSEER_*`.
- [x] `COMMANDS.md` e `deploy/runners/README.md` corrigidos (script Windows inexistente).
- [x] `CHANGELOG.md` e `VERSION` actualizados para 5.8.2.

### Pendente

- [ ] Deploy WS1207 bloqueado: SSH `DQSI@WS1207` indisponível a partir de prod e desta máquina (HP-Z2-EF). Executar manualmente na consola WS1207.
- [ ] Confirmar `payload.task_scheduler` em `/v1/read/heartbeats?limit=1` após reprovisionar WS1207.

### Deploy prod (2026-06-17)

- [x] `git pull`, `docker compose -f docker-compose.prod.yml up --build -d`, health OK.
- [x] `POST /v1/catalog/reconcile` com `sync_remote:false` (medidata_pipeline actualizado; sync remoto falhou por DNS WS1207 no prod).
- [ ] WS1207: comandos em `COMMANDS.md` secção Medidata.

### Próximos Passos

1. Push ambos repos.
2. SSH prod: `git pull`, `docker compose -f docker-compose.prod.yml up --build -d`, reconcile.
3. WS1207: pull repos, reprovisionar runner Medidata, heartbeat.
