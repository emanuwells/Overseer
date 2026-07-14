# Estrutura Operacional

## Visão Geral

Este documento descreve a estrutura operacional do projeto Overseer, incluindo responsabilidades, fronteiras e convenções.

## Stack Técnica

- **Backend**: Python (FastAPI)
- **Frontend**: HTML/CSS/JS vanilla
- **Base de Dados**: PostgreSQL
- **Runtime**: Docker-first
- **Monitorização**: Overseer self-hosted

## Módulos Principais

| Módulo | Responsabilidade |
|---|---|
| `src/overseer_api/` | API REST FastAPI |
| `src/overseer_core/` | Lógica de negócio central |
| `src/overseer_monitor/` | Monitorização de pipelines |
| `src/overseer_agent/` | Agente de execução |
| `src/overseer_sdk/` | SDK para integração |
| `frontend/` | Dashboard web |
| `runtime/` | Runtime de triggers |

## Fronteiras

- API expõe endpoints REST para gestão de runs, pipelines e deployments
- Core contém lógica de domínio pura, sem dependências de framework
- Monitor recolhe telemetria de pipelines externos
- Agent executa em runners remotos
- SDK permite integração programática

## Convenções de Código

- Python: PEP 8, type hints, docstrings em inglês técnico
- Frontend: vanilla JS, CSS modular, HTML semântico
- API: RESTful, OpenAPI spec em `openapi/overseer-api.yaml`
- Testes: pytest em `tests/`

## Diretrizes de Arquitetura

1. Separar lógica de domínio de infraestrutura
2. API thin, lógica em serviços
3. Base de dados via ORM com migrações
4. Configuração por ambiente via env vars
5. Logs estruturados em JSON para produção