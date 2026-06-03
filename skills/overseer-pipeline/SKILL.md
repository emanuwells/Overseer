---
name: overseer-pipeline
description: Integrar um pipeline no Overseer (YAML, lineage, secrets, API).
---

# Skill: Integrar pipeline no Overseer

## Quando usar

Ao criar ou migrar um pipeline para o runtime Overseer.

## Passos

1. Copiar `pipelines/_template/` para `pipelines/<pipeline_id>/`.
2. Preencher `pipeline.yaml`: `pipeline_id`, `name`, `owner`, `criticality`, `schedule`, `entrypoint`, `runner_host`.
3. Implementar `src/main.py` com `LineageEmitter` (`@@OVERSEER_MODULE@@`) em cada fase.
4. Configurar `secrets/database.json` e `secrets/slack.json` (nunca versionar).
5. Testar: `python orchestrator.py run <pipeline_id>`.
6. Validar telemetria via API: `GET /v1/monitoring/full` (não depender de JSON exportado).
7. Registar runner remoto: `python -m overseer_agent heartbeat` + `consume-triggers`.

## Contratos

- Telemetria: schema `Overseer`, tabelas `pipeline_runs`, `pipeline_module_events`.
- Triggers: `POST /v1/triggers` ou fila `orchestrator_triggers_local`.
- Excepção: pipelines que escrevem em schema `MAIATRON` (ex. `webapp_medidata`) mantêm DB target documentado no PRD.
