# ADR 0001 — Refactor Para Overseer Core API

## Estado

Aceite.

## Contexto

O Overseer tinha acumulado fluxos antigos de exportação `DB -> JSON`, frontend externo MAIATRON, scheduler CLI e escrita direta na base de dados. O novo objetivo é simplificar o produto sem perder capacidade operacional: observar, escrever telemetria, orquestrar pipelines e mostrar o estado local num frontend moderno.

## Decisão

O Overseer passa a ter uma FastAPI única com três superfícies:

- `/v1/read/*` para leitura operacional;
- `/v1/events/*` para ingest de runs, módulos, logs e heartbeats;
- `/v1/orchestrate/*` para triggers e execução de pipelines.

O schema canónico passa para tabelas `overseer_*`, criadas por SQLAlchemy no arranque. MariaDB continua a ser a base local suportada por Docker, mas o acesso por SQLAlchemy prepara migração futura para PostgreSQL ou outro dialecto compatível.

## Consequências

- O frontend local passa a ser React/Vite servido em `/ui/`.
- O fluxo MAIATRON/JSON/export deixa de ser contrato suportado.
- Pipelines podem integrar por SDK Python ou CLI `overseer-agent`.
- `microsoft_forms_2_datalake` fica como exemplo real; pipelines e docs legadas fora de escopo foram removidas.
