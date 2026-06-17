# Todo

Estado operacional das iterações em curso.

Não usar este ficheiro como histórico completo. Manter apenas tarefas úteis para execução, validação ou continuidade.

## Iteração Atual

**Data:** 2026-06-17  
**Estado:** Validada localmente  
**Risco:** Médio

### Objetivo

- Enviar inventário read-only do Task Scheduler Windows no heartbeat do Overseer e mostrá-lo na vista Ambiente.

### Feito

- [x] Criado `scripts/windows/collect-taskscheduler-info.ps1` para observar tasks por `task_name`, `run_ps` ou `task_match`.
- [x] `scripts/windows/heartbeat.ps1` passa a anexar `payload.task_scheduler` e mantém heartbeat mesmo se a recolha falhar.
- [x] `overseer-agent heartbeat --payload-file` junta payload local ao payload padrão.
- [x] Vista Ambiente mostra resumo Task Scheduler por host e detalhe por pipeline.
- [x] Testes adicionados para payload externo, payload inválido, persistência e leitura do inventário.

### Pendente

- [ ] Validar em `WS1207` com `.\scripts\windows\heartbeat.ps1`.
- [ ] Confirmar em `/v1/read/heartbeats?limit=1` que `payload.task_scheduler` contém os pipelines do `catalog.json`.
- [ ] Após deploy, reconciliar catálogo e re-provisionar `WS1207` se houver alterações de agenda.

### Bloqueios / Riscos

- Não foi executado deploy, SSH nem validação real no Task Scheduler de `WS1207` nesta iteração local.
- A recolha é observacional; não cria, arranca, altera nem remove scheduled tasks.

### Próximos Passos

1. Correr `.\scripts\windows\provision-runners.ps1 -Register` na máquina Windows quando o repo estiver atualizado.
2. Correr `.\scripts\windows\heartbeat.ps1`.
3. Confirmar `payload.task_scheduler` na API e no separador `Ambiente > Task Scheduler`.
