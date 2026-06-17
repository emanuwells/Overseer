# Todo

Estado operacional das iterações em curso.

## Iteração Atual

**Data:** 2026-06-17  
**Estado:** Concluída  
**Risco:** Médio

### Objetivo

- Identificar padrões duplicados no código e refactorar em utilitários partilhados (v5.8.3).

### Feito

- [x] Análise completa de duplicação no código-fonte.
- [x] `helpers.py`: `env_flag()` e `safe_metadata()` como utilitários partilhados.
- [x] `runner_ssh.py`: `_dispatch_ssh()` unifica processamento de saída SSH.
- [x] `store.py`: `_get_row()` unifica 5 funções `get_*`; `safe_metadata()` em 5 locais.
- [x] `slack_alerts.py`: `_send_slack_alert()` consolida boilerplate; `env_flag()` em 3 módulos.
- [x] `deployment_health.py`, `pipeline_inventory.py`, `runner_catalog.py`, `orchestrate.py`: `safe_metadata()`.
- [x] 85 testes passam sem modificação.
- [x] `CHANGELOG.md` e `VERSION` actualizados para 5.8.3.

### Pendente anterior (v5.8.2)

- [ ] Deploy WS1207 bloqueado: SSH `DQSI@WS1207` indisponível a partir de prod e desta máquina (HP-Z2-EF).
- [ ] Confirmar `payload.task_scheduler` em `/v1/read/heartbeats?limit=1` após reprovisionar WS1207.

### Próximos Passos

1. Merge do PR de refactoring.
2. Deploy prod: `git pull`, rebuild, reconcile.
