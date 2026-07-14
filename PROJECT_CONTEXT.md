# Contexto do projeto

## Identidade

O Overseer é um sistema de observabilidade para pipelines e DAGs externos. Reúne numa API e numa interface web a topologia declarada, o histórico de execuções e os sinais necessários para compreender o estado de cada deployment.

O projeto é Docker-first, escrito maioritariamente em Python e preparado para runners heterogéneos. A documentação pública e os exemplos são agnósticos; infraestrutura, hosts, catálogos e credenciais reais vivem fora do Git.

## Objetivo e utilizadores

O sistema deve responder de forma rápida e auditável:

1. que pipelines estão registados e em que hosts existem;
2. qual foi o resultado das execuções recentes;
3. onde existe uma falha ou quebra de cadência;
4. que módulos, logs e metadados explicam esse estado.

Destina-se a equipas de operação, desenvolvimento e suporte que mantêm pipelines externos. A interface é read-only; ações de execução continuam sob controlo do runner e exigem autenticação na API.

## Escopo funcional

Incluído:

- catálogo de pipelines, módulos, dependências e deployments;
- runs com estado, duração, host, origem e metadados;
- eventos de módulos e logs associados a uma run;
- heartbeats de agentes e inventário operacional;
- fila opcional de triggers para runners autorizados;
- deteção de falhas abertas e deployments stale;
- frontend de consulta, SDK Python, agente e monitor;
- alertas imediatos e digest diário por Slack.

Fora de escopo:

- executar o código de negócio dos pipelines;
- guardar segredos de pipelines;
- substituir o scheduler, CI ou orquestrador de origem;
- editar catálogos através do frontend;
- agregar logs sem relação com uma run.

## Stack e componentes

| Área | Tecnologia | Responsabilidade |
|---|---|---|
| API | FastAPI e Uvicorn | Contrato HTTP /v1, autenticação e frontend |
| Domínio | Python | Regras de catálogo, runs, saúde e triggers |
| Persistência | SQLAlchemy | Acesso transacional e compatibilidade SQL |
| Base de dados | MariaDB | Estado oficial no Compose |
| SDK e agente | Python e HTTPX | Integração e consumo remoto |
| Interface | HTML, CSS e JavaScript | Consulta operacional sem build Node.js |
| Operação | Docker Compose | API, base de dados, volumes e rede |
| Testes | pytest | Contrato, persistência, integrações e regressões |

## Arquitetura e fluxos

    pipelines e runners -- HTTPS/token --> Overseer API
           ^                                    |
           | triggers opcionais                 | SQLAlchemy
           |                                    v
           +------------------------------- MariaDB
                                                |
                                                +--> UI estática
                                                +--> Slack opcional

Fluxo de catálogo:

1. o integrador envia identidade, módulos, edges e schedule;
2. a API normaliza pipeline_id e host_id;
3. a persistência atualiza o deployment sem perder o histórico;
4. a UI apresenta a topologia declarada.

Fluxo de run:

1. o pipeline abre a run;
2. envia progresso, módulos e logs relevantes;
3. fecha a run com um estado terminal;
4. a API recalcula a saúde do deployment;
5. uma falha pode gerar um alerta Slack e uma execução posterior bem-sucedida pode gerar a resolução.

Fluxo de digest:

1. a aplicação calcula o próximo horário em Europe/Lisbon;
2. agrega runs das últimas 24 horas, falhas abertas e pipelines stale;
3. omite heartbeats e triggers em fila para reduzir ruído;
4. só menciona o canal quando existem falhas abertas ou deployments fora de cadência.

## Organização do código

- **src/overseer_api/**: aplicação FastAPI, lifespan e routers;
- **src/overseer_core/**: persistência, saúde, catálogos, Slack e regras partilhadas;
- **src/overseer_sdk/**: cliente HTTP e helpers de integração;
- **src/overseer_agent/**: heartbeat e consumo de triggers;
- **src/overseer_monitor/**: integração para processos observados;
- **frontend/**: dashboard e páginas de detalhe;
- **openapi/**: contrato público versionado;
- **docker/**: Dockerfile e variantes Compose;
- **deploy/runners/**: catálogo público de exemplo;
- **scripts/**: operação, manutenção e onboarding;
- **tests/**: testes unitários e de integração local.

## Contratos e invariantes

- /v1/health é o endpoint de health canónico.
- pipeline_id identifica o pipeline lógico; host_id distingue deployments.
- Uma run pertence a um pipeline e host e possui run_id único.
- Estados terminais são normalizados para ok, warning ou failed.
- O frontend consome a API e não escreve diretamente na base de dados.
- Catálogos privados são montados em /app/deploy/runners.
- Runtime e volumes não dependem da revisão Git.
- Alterações ao contrato público exigem atualização de OpenAPI e testes.

## Configuração e dados privados

| Variável | Regra operacional |
|---|---|
| OVERSEER_API_TOKEN | Obrigatória fora de desenvolvimento; nunca versionada |
| OVERSEER_DB_URL | Aponta para a base de dados do ambiente |
| OVERSEER_CORS_ORIGINS | Deve listar origens explícitas em produção |
| OVERSEER_RUNNERS_DIR | Diretório privado obrigatório em produção |
| OVERSEER_RUNTIME_DIR | Armazenamento persistente fora do checkout |
| OVERSEER_SSH_SYNC_ENABLED | Desativado por defeito; exige SSH privado |
| OVERSEER_SLACK_WEBHOOK_URL | Segredo opcional, nunca registado em logs |
| OVERSEER_SLACK_DIGEST_ENABLED | Controlo explícito do resumo diário |

O Git contém apenas o template de ambiente, catálogos genéricos e exemplos com placeholders. Nomes de pessoas, IPs, hosts, caminhos locais, tokens, webhooks, dumps e referências a sistemas privados não são documentação aceitável.

## Ambientes

### Desenvolvimento local

Usa .env criado a partir do exemplo, catálogos em deploy/runners/ e runtime em runtime/. Estes valores permitem executar o sistema sem infraestrutura externa.

### Produção

Usa configuração, catálogos e runtime fora do checkout. A imagem é construída a partir de uma revisão identificável. Antes de atualizar devem existir backup verificável, SHA atual, referência da imagem e plano de rollback. Volumes não são removidos durante deploy ou rollback.

## Segurança

- endpoints de escrita exigem token;
- segredos são fornecidos por ambiente ou ficheiros privados ignorados;
- mensagens e logs não incluem tokens, passwords, cookies ou chaves;
- sincronização SSH é opcional e usa permissões mínimas;
- o frontend é read-only e não concede autorização operacional;
- exposição pública requer TLS e controlo de acesso a montante.

As vulnerabilidades seguem o processo de .github/SECURITY.md.

## Qualidade e critérios de aceitação

    python -m pytest -q
    docker compose --project-directory . -f docker/docker-compose.yml config
    docker compose --project-directory . -f docker/docker-compose.official.yml config
    docker compose --project-directory . -f docker/docker-compose.yml build

Devem ainda ser revistos o diff, os ficheiros rastreados, referências quebradas e dados identificáveis. Scripts exigem validação de sintaxe proporcional. Produção exige health, base de dados, UI, catálogos e contentores estáveis.

## Decisões e limites de evolução

- A API e o modelo persistente são o núcleo estável; integrações adaptam-se ao contrato.
- A configuração operacional real permanece externa ao Git.
- O frontend continua read-only até existir decisão arquitetural e autorização adequada.
- A publicação do código mantém licença proprietária.
- Refactors estruturais preservam comportamento, são faseados e têm rollback.

As decisões vivem em docs/adr/ e docs/architecture/. Os comandos suportados estão em COMMANDS.md; trabalho e aprendizagens ficam em tasks/.
