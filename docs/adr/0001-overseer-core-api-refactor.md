# ADR 0001 — Núcleo API E Observabilidade DAG

> **Nota histórica:** decisões sobre frontend estático e ausência de Vite foram **substituídas** pela SPA React (Vite) documentada em `docs/architecture/frontend.md`. O restante (API `/v1`, tabelas `overseer_*`, pipelines externos) mantém-se válido.

## Estado

Aceite.

## Contexto

O Overseer acumulou fluxos antigos de exportação, frontend externo, scheduler CLI, escrita direta na base de dados e exemplos de pipelines dentro do próprio repositório. O objetivo atual é manter o Overseer como núcleo operacional independente: observar pipelines externos, receber catálogo DAG e telemetria por API, persistir eventos e expor uma UI local.

## Decisão

- Manter uma FastAPI única com routers separados para leitura, catálogo, eventos, health e triggers.
- Usar SQLAlchemy e tabelas `overseer_*` como contrato persistente.
- Registar catálogo de pipelines por `POST /v1/catalog/pipelines`, com nodes e edges de DAG.
- Interpretar `overseer_modules.module_id` como estado runtime de um node do DAG.
- Servir frontend estático em `/ui/`, com `/` e `/ui` a redirecionarem para `/ui/dashboard.html`.
- Não executar código de pipelines dentro do Overseer; pipelines externos enviam catálogo e telemetria por API.
- Manter triggers como sinais operacionais, não como execução local.
- Manter Docker Compose como fluxo principal para API, frontend e MariaDB local.

## Consequências

- Repositórios de pipelines deixam de precisar de ser copiados para `pipelines/`.
- YAML deixa de ser contrato obrigatório; o registo por API passa a ser a fonte principal do catálogo.
- O endpoint `/v1/orchestrate/pipelines/{pipeline_id}/run` deixa de existir.
- O Dockerfile deixa de ter fase Node/Vite porque o frontend é estático.
- Dados de pipelines reais só aparecem na UI depois de registo por `/v1/catalog/pipelines` e emissão de eventos por `/v1/events/*`.

## Alternativas Rejeitadas

- Manter execução local por subprocesso no Overseer: acoplava o núcleo ao código e dependências de cada pipeline.
- Manter pipeline de exemplo no núcleo: confundia demo com contrato operacional.
- Manter frontend React/Vite: acrescentava build Node sem necessidade para o estado atual da UI.
