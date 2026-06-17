# Lessons

Aprendizagens reutilizáveis para reduzir erro em iterações futuras.

Registar apenas informação com valor futuro. Não duplicar changelog, logs extensos ou tarefas temporárias.

## Regras

- Usar entradas curtas e pesquisáveis.
- Registar causa e correção quando houver erro.
- Não guardar segredos, tokens, credenciais ou dados pessoais.
- Preferir padrões reutilizáveis a descrições circunstanciais.

## Entradas

### 2026-06-17 — Staleness depende de agenda real

**Contexto:** O `medidata_pipeline` ficou dias sem correr e não apareceu como `stale` porque estava marcado como `manual`.  
**Aprendizagem:** Pipelines monitorizados com SLA operacional devem ter cron real no catálogo; `manual` significa sem staleness automático.  
**Impacto:** Evita falsos negativos em pipelines Windows/Task Scheduler e mantém API, UI e Slack alinhados pela mesma regra.  
**Refs:** `deploy/runners/WS1207.yaml`, `src/overseer_core/deployment_health.py`, `src/overseer_core/slack_digest.py`

### 2026-06-17 — Inventário operacional deve viajar no heartbeat

**Contexto:** O Overseer precisava de observar o Task Scheduler Windows sem executar pipelines nem criar nova tabela.  
**Aprendizagem:** O payload JSON do heartbeat é o canal adequado para inventário periódico, autenticado e tolerante a falhas.  
**Impacto:** `overseer-agent heartbeat --payload-file` permite anexar dados locais preservando `agent_version` e `api_reachable`; falhas de recolha devem degradar só o bloco local, não o heartbeat.  
**Refs:** `scripts/windows/collect-taskscheduler-info.ps1`, `scripts/windows/heartbeat.ps1`, `src/overseer_agent/__main__.py`
