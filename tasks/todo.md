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

- [ ] Deploy prod Linux (pull, compose, reconcile).
- [ ] Deploy WS1207 (pull, install-runner, provision-runners, heartbeat).
- [ ] Validar `payload.task_scheduler` em `/v1/read/heartbeats?limit=1`.

### Próximos Passos

1. Push ambos repos.
2. SSH prod: `git pull`, `docker compose -f docker-compose.prod.yml up --build -d`, reconcile.
3. WS1207: pull repos, reprovisionar runner Medidata, heartbeat.
