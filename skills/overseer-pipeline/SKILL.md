---
name: overseer-pipeline
description: Integrar um pipeline externo no Overseer por API.
---

# Skill: Integrar Pipeline No Overseer

## Quando usar

Ao criar ou migrar um pipeline externo para observabilidade no Overseer.

## Passos

1. Copiar `templates/pipeline-repo/` para a raiz do repositório do pipeline.
2. Criar `.env.overseer` a partir de `.env.overseer.example`, sem versionar segredos reais.
3. Registar o DAG com `overseer.register_catalog(nodes=[...], edges=[...])` ou `POST /v1/catalog/pipelines`.
4. Instrumentar runs com `OverseerClient`, `overseer.run()` e `overseer.step()`.
5. Registar logs relevantes em `/v1/events/logs` e heartbeats em `/v1/events/heartbeat`.
6. Validar leitura: `GET /v1/read/pipelines/{pipeline_id}/dag`, `GET /v1/read/runs` e `GET /v1/read/runs/{run_id}`.
7. Validar o frontend local em `http://127.0.0.1:8090/ui/dashboard.html`.

## Contratos

- Catálogo DAG: API `POST /v1/catalog/pipelines`.
- Telemetria: API `POST /v1/events/*`.
- Leitura: API `GET /v1/read/*`.
- Triggers: API `POST /v1/orchestrate/triggers`, sem execução local de código.
- Base de dados: tabelas `overseer_*`, criadas por SQLAlchemy.
- Docker: o fluxo suportado é `overseer-up.cmd`, `scripts/overseer-up.ps1`, `scripts/overseer-up.sh` ou `docker compose up --build -d`.
