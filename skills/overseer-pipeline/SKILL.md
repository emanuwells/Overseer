---
name: overseer-pipeline
description: Integrar um pipeline no Overseer Core API.
---

# Skill: Integrar Pipeline No Overseer

## Quando usar

Ao criar ou migrar um pipeline para o runtime Overseer.

## Passos

1. Criar `pipelines/<pipeline_id>/pipeline.yaml` com `pipeline_id`, `name`, `owner`, `criticality`, `entrypoint` e, se necessário, `entrypoint_windows`.
2. Implementar `src/main.py` com `OverseerClient`, `OverseerMonitor` ou `LineageEmitter` (`@@OVERSEER_MODULE@@`) para registar módulos e eventos.
3. Configurar segredos apenas fora do Git; usar `.env.example` para nomes de variáveis e valores fictícios.
4. Testar localmente via API: `python -m overseer_agent run <pipeline_id> --foreground`.
5. Validar leitura: `GET /v1/read/runs` e `GET /v1/read/runs/{run_id}`.
6. Validar ações operacionais no frontend local em `http://127.0.0.1:8090/ui/`.
7. Usar `python -m overseer_agent heartbeat` para registar agentes externos.

## Contratos

- Telemetria: API `POST /v1/events/*`.
- Leitura: API `GET /v1/read/*`.
- Orquestração: API `POST /v1/orchestrate/*`.
- Base de dados: tabelas `overseer_*`, criadas por SQLAlchemy.
- Docker: o fluxo suportado é `overseer-up.cmd`, `scripts/overseer-up.ps1`, `scripts/overseer-up.sh` ou `docker compose up --build -d`.
