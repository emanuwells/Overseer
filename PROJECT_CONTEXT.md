# Contexto do projeto

Contexto técnico vivo do Overseer. Mantém-se alinhado com [`AGENTS.md`](AGENTS.md), [`COMMANDS.md`](COMMANDS.md) e [`docs/architecture/`](docs/architecture/).

## Identificação

- **Nome do projeto:** Overseer
- **Descrição curta:** observabilidade Docker-first para pipelines e DAGs externos
- **Responsável:** programador solo com apoio de equipa IA
- **Versão atual:** ver [`VERSION`](VERSION)
- **Estado:** produção / manutenção

## Domínio

- **Problema que resolve:** falta de visão unificada sobre pipelines distribuídos, runs, falhas e cadência
- **Utilizadores principais:** operação, desenvolvimento e suporte de pipelines externos
- **Regras de negócio críticas:**
  - `pipeline_id` identifica o pipeline lógico; `host_id` distingue deployments
  - estados terminais normalizados: ok, warning, failed
  - interface read-only; alterações via API autenticada, runners ou CLI
  - digest Slack omite heartbeats e triggers em fila; digest e alertas imediatos mencionam `@channel` por defeito
- **Dados sensíveis:** tokens API, webhooks Slack, credenciais DB, chaves SSH, catálogos reais
- **Integrações externas:** runners HTTP, agente Overseer, Slack, sincronização SSH opcional

## Stack

| Camada | Tecnologia | Versão | Observações |
|---|---|---|---|
| Frontend | React, TypeScript, Vite, React Router, TanStack Query, Tailwind CSS | 19 / 5 / 6 | SPA read-only em `/ui/` |
| Backend | FastAPI, Uvicorn, Python | 3.11+ | API canónica `/v1` |
| Base de dados | MariaDB, SQLAlchemy | 10.11 | Persistência oficial no Compose |
| Infraestrutura | Docker Compose | — | API, DB, volumes, nginx opcional |
| Testes | pytest | — | Contrato, persistência, integrações |

## Arquitetura

Documentação técnica em `docs/architecture/`:

- Visão geral: [`docs/architecture/overview.md`](docs/architecture/overview.md)
- Frontend: [`docs/architecture/frontend.md`](docs/architecture/frontend.md)
- Backend: [`docs/architecture/backend.md`](docs/architecture/backend.md)
- Base de dados: [`docs/architecture/database.md`](docs/architecture/database.md)
- Deploy: [`docs/architecture/deployment.md`](docs/architecture/deployment.md)
- Decisões: [`docs/architecture/decisions.md`](docs/architecture/decisions.md) e [`docs/adr/`](docs/adr/)

Fluxo principal:

    pipelines e runners -- HTTPS/token --> Overseer API
           ^                                    |
           | triggers opcionais                 | SQLAlchemy
           |                                    v
           +------------------------------- MariaDB
                                                |
                                                +--> UI React (SPA)
                                                +--> Slack opcional

## Comandos reais

Manter [`COMMANDS.md`](COMMANDS.md) atualizado. Validação mínima habitual:

```bash
python -m pytest -q
cd frontend && npm ci && npm run build
docker compose --project-directory . -f docker/docker-compose.yml config
docker compose --project-directory . -f docker/docker-compose.yml build
```

## Ferramentas IA

- **Adaptador ativo:** opcional via `scripts/activate-ai-adapter.*`
- **Motivo:** compatibilidade com IDE/agente sem duplicar o núcleo do repo
- **Observações:** adaptadores vivem em `tools/ai-adapters/`; contrato canónico em `AGENTS.md`

## Riscos

| Risco | Impacto | Mitigação |
|---|---|---|
| Exposição de segredos no Git | compromisso de tokens e infraestrutura | `.env` ignorado, templates sem valores reais, revisão de diff |
| Perda de dados em deploy | indisponibilidade operacional | backup verificável, sem `down -v`, rollback documentado |
| Divergência docs/código | decisões erradas por agentes ou operadores | código e testes como fonte de verdade; corrigir docs |
| Regressão na SPA | UI inutilizável em produção | build Vite no Docker, smoke `/ui/`, pytest de redirects |

## Restrições

- configuração operacional real (`OVERSEER_RUNNERS_DIR`, runtime, segredos) fora do Git
- frontend permanece read-only até decisão arquitetural explícita
- produção, SSH e operações destrutivas exigem confirmação
- documentação em português europeu; identificadores técnicos em inglês

## Decisões em aberto

- visibilidade pública do repositório GitHub (pendente sessão autenticada)
- evolução de escrita na UI (fora de escopo actual)

## Critérios de qualidade

- **Testes obrigatórios:** `python -m pytest -q`
- **Build obrigatório:** `cd frontend && npm run build`; Docker build em alterações de imagem
- **Review obrigatória:** diff, referências, ausência de segredos e dados identificáveis
- **Segurança:** tokens nunca versionados; CORS explícito em produção
- **Documentação:** README, PROJECT_CONTEXT, CHANGELOG e arquitetura quando comportamento ou comandos mudam

## Organização do código

- **src/overseer_api/**: aplicação FastAPI, lifespan e routers
- **src/overseer_core/**: persistência, saúde, catálogos, Slack
- **src/overseer_sdk/**, **src/overseer_agent/**, **src/overseer_monitor/**: integração
- **frontend/src/**: SPA React
- **openapi/**: contrato público versionado
- **docker/**, **deploy/**, **scripts/**, **tests/**: operação e qualidade

## Invariantes

- `/v1/health` é o endpoint de health canónico
- catálogos privados montados em `/app/deploy/runners`
- runtime e volumes independentes da revisão Git
- alterações ao contrato público exigem OpenAPI e testes actualizados
