# Visão Geral Da Arquitetura

## Objetivo Do Sistema

O Overseer é um núcleo Docker-first de observabilidade operacional para pipelines e DAGs externos. O sistema recebe catálogo, eventos, runs, heartbeats e triggers por API, persiste o estado operacional em base de dados relacional e disponibiliza uma UI local para leitura e diagnóstico.

O Overseer não executa código de pipelines no núcleo. Pipelines, runners e agentes externos registam metadados e telemetria através dos contratos HTTP e CLI.

## Contexto

| Área | Descrição |
|---|---|
| Domínio | Observabilidade, catálogo e operação de pipelines externos |
| Utilizadores principais | Operação técnica, maintainer do projeto e agentes de automação |
| Sistemas externos | Pipelines, runners Linux/Windows, Task Scheduler, SSH, Slack e base de dados relacional |
| Dados críticos | Runs, eventos, heartbeats, catálogo DAG, triggers e configuração operacional |
| Restrições técnicas | Docker-first, UI read-only, API versionada em `/v1`, segredos fora do Git |

## Componentes

| Componente | Responsabilidade | Tecnologia |
|---|---|---|
| Frontend | Consulta read-only de estado operacional, deployments, lineage e detalhe de runs | HTML, CSS e JavaScript estático |
| API | Contratos HTTP para leitura, catálogo, eventos, health e triggers | FastAPI, Uvicorn |
| Persistência | Guardar catálogo, telemetria, triggers e estado operacional | MariaDB local por Compose; SQLAlchemy para dialectos compatíveis |
| SDK / Agent | Emitir telemetria, validar manifests, enviar heartbeats e operar runners | Python, HTTPX, CLI instalável |
| Operação | Arranque local/prod, provisionamento de runners e manutenção | Docker Compose, scripts PowerShell/Bash/Python |

## Fluxo Principal

```text
Pipeline externo / Agent
  -> API /v1/catalog, /v1/events, /v1/orchestrate
  -> Base de dados overseer_*
  -> API /v1/read
  -> Frontend estático /ui
```

## Fronteiras

### Dentro Do Sistema

- API FastAPI e routers em `src/overseer_api/`.
- Serviços de domínio e persistência em `src/overseer_core/`.
- SDK, agent e monitorização auxiliar em `src/overseer_sdk/`, `src/overseer_agent/` e `src/overseer_monitor/`.
- Frontend estático em `frontend/`.
- Templates de integração para runners e pipelines em `docs/resources/examples/overseer/`.
- Configuração Docker em `docker/`; runners e nginx em `deploy/`.

### Fora Do Sistema

- Código real dos pipelines observados.
- Execução local de DAGs no núcleo Overseer.
- Segredos reais, chaves SSH, tokens e credenciais.
- Configurações reais de produção fora do contrato documentado.

## Riscos Arquiteturais

- Divergência entre catálogo registado e pipelines reais quando runners externos não emitem telemetria.
- Dependência operacional de SSH/Task Scheduler para alguns runners Windows.
- Configuração incorreta de tokens ou URLs pode impedir escrita de telemetria sem afetar a UI read-only.
- Evolução de schema deve preservar tabelas `overseer_*` e ser validada por testes.

## Dívida Técnica Conhecida

- Governação operacional mínima em `AGENTS.md` e `docs/ai/`.
- A documentação de arquitetura é inicial e deve acompanhar alterações futuras de API, persistência, Docker ou frontend.
