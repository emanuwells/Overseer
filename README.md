# Overseer

![Estado](https://img.shields.io/badge/estado-estável-2ecc71)
![Versão](https://img.shields.io/badge/versão-5.8.27-3498db)
![Licença](https://img.shields.io/badge/licença-proprietária-lightgrey)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)

O Overseer é um serviço Docker-first de observabilidade para pipelines e DAGs externos. Centraliza catálogos, execuções, módulos, logs e sinais operacionais numa API, persiste o estado e apresenta-o numa interface web de consulta.

O serviço observa pipelines; não incorpora o respetivo código nem substitui o orquestrador que os executa. Esta separação permite integrar processos Python, tarefas agendadas, jobs de CI ou outros runners sem acoplar o seu ciclo de vida ao Overseer.

## Contrato para agentes e contribuidores

Trabalho neste repositório segue [`AGENTS.md`](AGENTS.md): hierarquia de autoridade, fontes de verdade, classificação de risco, fluxo operacional e modelo de equipa IA. Antes de alterações não triviais, leia também [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) e [`COMMANDS.md`](COMMANDS.md).

## Documentação normativa

| Documento | Finalidade |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Contrato operacional para agentes e ferramentas de IA |
| [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) | Contexto técnico vivo do produto |
| [`COMMANDS.md`](COMMANDS.md) | Comandos reais de desenvolvimento, testes e deploy |
| [`docs/architecture/`](docs/architecture/) | Arquitetura por camada |
| [`docs/ai/DAILY_AGENT_WORKFLOW.md`](docs/ai/DAILY_AGENT_WORKFLOW.md) | Fluxo diário recomendado para agentes |

## O que resolve

- oferece uma visão comum de pipelines distribuídos por vários hosts;
- regista o início, progresso e resultado de cada execução;
- representa módulos e dependências de um DAG;
- identifica falhas abertas e pipelines fora da cadência esperada;
- mantém uma interface web read-only para consulta operacional;
- disponibiliza SDK, agente e exemplos para integração externa;
- suporta triggers opcionais, consumidos pelos runners autorizados;
- envia alertas de falha e um digest diário para Slack.

Não é um motor de workflows, um gestor de segredos ou um substituto de uma plataforma de logs. O pipeline continua responsável pela execução, pelos retries de negócio e pelo tratamento dos seus dados.

## Arquitetura

    pipeline ou runner
            | catálogo, runs, módulos, logs, heartbeat
            v
       Overseer API ------> MariaDB
            |                  |
            +------> interface web read-only (React SPA)
            +------> Slack (opcional)

A API FastAPI é o ponto de entrada canónico. A camada de domínio e persistência vive em **src/overseer_core/**; o SDK e o agente reutilizam o mesmo contrato HTTP. O frontend é uma SPA React construída com Vite e servida em `/ui/`. Consulte [Arquitetura](docs/architecture/overview.md).

## Arranque local

### Pré-requisitos

- Docker Engine ou Docker Desktop com Compose;
- Git;
- Python 3.11 ou superior para desenvolvimento e testes;
- Node.js 20+ apenas para desenvolvimento frontend (`npm run dev`).

Em Linux ou macOS:

    cp docs/resources/templates/.env.example .env
    docker compose --project-directory . -f docker/docker-compose.yml up --build -d

No PowerShell:

    Copy-Item docs/resources/templates/.env.example .env
    docker compose --project-directory . -f docker/docker-compose.yml up --build -d

Confirme o arranque:

    curl http://127.0.0.1:8090/v1/health

Serviços disponíveis por defeito:

- API e health: **http://127.0.0.1:8090/v1/health**;
- interface: **http://127.0.0.1:8090/ui/**;
- contrato OpenAPI: **openapi/overseer-api.yaml**;
- MariaDB local: porta **3307** do host.

Os valores do exemplo destinam-se exclusivamente a desenvolvimento. Antes de usar outro ambiente, substitua tokens e passwords e restrinja as origens CORS.

### Desenvolvimento frontend

Com a API a correr localmente:

```bash
cd frontend
npm ci
npm run dev
```

O servidor Vite faz proxy de `/v1` para a API. Para produção ou Docker, `npm run build` gera `frontend/dist/`, copiado pela imagem.

## Configuração

| Variável | Finalidade | Desenvolvimento |
|---|---|---|
| OVERSEER_API_PORT | Porta HTTP publicada pelo Compose | 8090 |
| OVERSEER_API_TOKEN | Token exigido nos endpoints protegidos | valor local do exemplo |
| OVERSEER_CORS_ORIGINS | Origens autorizadas, separadas por vírgulas | * |
| OVERSEER_DB_URL | Ligação SQLAlchemy à base de dados | MariaDB do Compose |
| OVERSEER_RUNNERS_DIR | Diretório privado com hosts e catálogos | ./deploy/runners |
| OVERSEER_RUNTIME_DIR | Estado persistente fora da imagem | ./runtime |
| OVERSEER_SSH_SYNC_ENABLED | Ativa sincronização remota por SSH | 1 |
| OVERSEER_SLACK_WEBHOOK_URL | Webhook de Slack, opcional | não definido |
| OVERSEER_SLACK_DIGEST_ENABLED | Ativa o resumo diário | herda a presença do webhook |
| OVERSEER_SLACK_DIGEST_HOUR | Hora do digest em Europe/Lisbon | 8 |
| OVERSEER_SLACK_DIGEST_MINUTE | Minuto do digest | 30 |

O digest inclui resultados, falhas abertas e pipelines fora de cadência. Heartbeats e triggers em fila permanecem consultáveis pela API e pela interface, mas não são enviados no resumo. Um digest saudável não menciona @channel; a menção fica reservada a situações acionáveis.

### Configuração privada

**OVERSEER_RUNNERS_DIR** deve apontar para um diretório fora do checkout em produção. Esse diretório contém **hosts.yaml** e um catálogo **host-id.yaml** por host e é montado no contentor em **/app/deploy/runners**. O repositório inclui apenas exemplos genéricos.

**OVERSEER_RUNTIME_DIR** também deve apontar para armazenamento persistente fora do checkout. Assim, uma atualização ou reversão de código não move nem elimina estado operacional.

Nunca versione `.env`, tokens, webhooks, chaves SSH, catálogos reais ou cópias da base de dados.

## Integrar um pipeline

Uma integração típica:

1. regista o catálogo e a topologia do pipeline;
2. abre uma run antes da execução;
3. comunica módulos e logs relevantes;
4. fecha a run com ok, warning ou failed;
5. opcionalmente envia heartbeats e consome triggers.

O SDK Python reduz o código necessário, mas qualquer cliente HTTP pode usar a API `/v1`. Consulte [Integração de pipelines](docs/pipeline-integration.md), os [exemplos](docs/resources/examples/overseer/) e o contrato [OpenAPI](openapi/overseer-api.yaml).

## Desenvolvimento e qualidade

```bash
python -m pip install -r src/requirements.txt
python -m pip install -e ./src
python -m pytest -q
cd frontend && npm ci && npm run build
docker compose --project-directory . -f docker/docker-compose.yml config
docker compose --project-directory . -f docker/docker-compose.yml build
```

O backend usa FastAPI e SQLAlchemy. O frontend usa React, TypeScript, Vite, React Router e TanStack Query. Os restantes comandos suportados estão em [COMMANDS.md](COMMANDS.md).

## Estrutura do repositório

| Diretório | Conteúdo |
|---|---|
| src/ | API, domínio, persistência, SDK, agente e monitorização |
| frontend/ | SPA React (código-fonte e `dist/` após build) |
| openapi/ | contrato público da API |
| docker/ | imagem e ficheiros Compose |
| deploy/ | exemplos públicos de configuração operacional |
| runtime/ | estado local ignorado pelo Git |
| scripts/ | arranque, manutenção, integração e provisionamento |
| tests/ | testes automatizados |
| docs/ | arquitetura, operação, governação e exemplos |
| tasks/ | estado de trabalho e aprendizagens reutilizáveis |
| tools/ | adaptadores IA opcionais |

## Operação e produção

Uma atualização de produção deve preservar `.env`, catálogos privados, runtime, volumes e referência da imagem ativa. Valide primeiro a configuração Compose e o build num checkout paralelo. Depois da troca, confirme health, base de dados, interface, catálogos e estabilidade dos contentores.

O rollback restaura o checkout e a imagem anteriores, mantendo configuração e volumes. Não use `docker compose down -v` num procedimento normal de atualização. Consulte o [runbook](docs/ai/ops/RUNBOOK.md).

## Segurança, contribuição e licença

Consulte [.github/SECURITY.md](.github/SECURITY.md) para comunicar vulnerabilidades sem expor detalhes publicamente. As regras de contribuição estão em [docs/governance/CONTRIBUTING.md](docs/governance/CONTRIBUTING.md).

O código é publicado sob licença proprietária. A visibilidade do repositório não concede direitos de utilização, modificação ou redistribuição além dos expressamente indicados em [LICENSE](LICENSE).
