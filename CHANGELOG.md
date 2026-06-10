# Changelog

## [5.2.0] - 2026-06-10T14:30:00+01:00

### Higiene do repositório e alinhamento com AGENTS.md

**Motivo:**
Consolidar estrutura `.agents/` como fonte canónica, remover duplicados na raiz e apagar artefactos obsoletos documentados como removidos.

**Impacto:**
Policies, skills e handoff passam a viver apenas em `.agents/`. Referências em documentação atualizadas. Sem alteração de código de runtime.

**Alterações:**
- Removidos `SKILLS.md`, `CHANGELOG_POLICY.md` e `HANDOFF.md` da raiz (canónicos em `.agents/`).
- Removida pasta `skills/` legada (substituída por `.agents/skills/` e `.claude/skills/`).
- Removidos `overseer_deploy.tgz`, `frontend/landing.html` e `frontend/bruinops-prototype.html`.
- Removidas pastas vazias `config/` e `pipelines/` (shells sem ficheiros versionados).
- `.agents/policies/CHANGELOG_POLICY.md`: política consolidada com paths atualizados.
- `PROJECT_CONTEXT.md`, `README.md`, `.agents/skills/README.md`: referências corrigidas.
- `pyproject.toml`: `testpaths` e `norecursedirs` para evitar recolha acidental em `pipelines/`.
- Removidos scaffold templates: `README.template.md`, `PROJECT_CONTEXT.template.md`, `.gitignore.template`.
- `COMMANDS.md`: comandos reais do Overseer (substitui placeholders genéricos).
- `.gitignore`: `runtime/*.db` para artefactos locais de runtime.

**Ferramentas, MCP E Skills:**
- MCP: N/A — não aplicável.
- Skills: `repo-hygiene`, `stop-the-slop`, `professional-documentation`.

**Ficheiros Removidos Ou Obsoletos:**
- Duplicados na raiz, skills legadas, artefacto `.tgz`, frontend obsoleto, pastas vazias.

**Validação:**
- Auditoria manual contra `AGENTS.md` e `.agents/ops/STRUCTURE.md`.
- Skills `.agents/skills/` e `.claude/skills/` com 23 entradas em sync.
- `python -m pytest -q`: 36 passed.

---

## [5.1.0] - 2026-06-08T20:00:00+01:00

### Façade `/v1/monitoring/*` para WELLS_API e MAIATRON

**Motivo:**
WELLS_API Explorer, MAIATRON Overseer e Ops Center consomem `/v1/monitoring/*`; a API v5 expunha apenas `/v1/read/*`.

**Alterações:**
- `monitoring_export.py` — adaptador v5 → payload legacy (`fields`, `rows`, `overview`, `pipelines`, …).
- Router `GET /v1/monitoring/full`, `/details`, `/ops/fast`, `/ops/heavy`.
- Testes `tests/test_monitoring_export.py`.

---

## [5.0.0] - 2026-06-08T18:00:00+01:00

### host_id, runners fiáveis e frontend produtivo

**Motivo:**
Separar deployment por máquina (`host_id`) do `pipeline_id` lógico partilhado, corrigir agente Windows atrás de proxy corporativo, e alinhar dashboard/lineage com a última run por host.

**Impacto (breaking):**
- `pipeline_id` deixa de usar sufixo `__HOST` (ex. `medidata_pipeline__WS1207` → `medidata_pipeline` + `host_id=WS1207`).
- Correr `python scripts/migrate_pipeline_host_suffix.py` em produção antes de re-provisionar runners.
- Task Scheduler WS1207: `...\overseer-runners\medidata_pipeline\run.ps1`.

**Alterações:**
- Coluna `host_id` em pipelines, runs, modules, logs, heartbeats, triggers; DAG partilhado por `pipeline_id`.
- SDK/agente: `httpx` com `trust_env=False`; env lido em runtime; `NO_PROXY` nos templates Windows.
- `list_pipelines()` sem duplicados; `last_duration_sec`; lineage usa última run + nós blocked downstream.
- Frontend: coluna Host, nomes legíveis, deploy nginx via `scripts/deploy-nginx-frontend.sh`.

---

## [4.4.4] - 2026-06-08T15:30:00+01:00

### Migração Crontab e Windows Runner

**Motivo:**
Completar a migração Overseer no baze2 e estabilizar o wrapper Windows gerado (`run.ps1`).

**Impacto:**
- `provision-runners.sh` usa o Python do venv (evita `ModuleNotFoundError: yaml`).
- `update-crontab-overseer.py` ignora linhas já migradas (`# overseer:`).
- `run.ps1` gerado usa `python -m overseer_agent` (mesmo padrão que `heartbeat.ps1`).
- Script `setup-medidata-overseer.ps1` para onboarding WS1207.

**Alterações:**
- `scripts/provision-runners.sh`, `scripts/update-crontab-overseer.py`, `scripts/provision_runners.py`.
- `scripts/windows/setup-medidata-overseer.ps1`.

---

## [4.4.3] - 2026-06-08T14:00:00+01:00

### Fix Scripts Windows (`RepoRoot` e helpers partilhados)

**Motivo:**
`provision-runners.ps1` calculava mal a raiz do repo (`scripts\scripts\provision_runners.py`), impedindo o provisionamento no Windows após pull.

**Impacto:**
Pull + `provision-runners.ps1 -Register` funciona sem workaround manual. Heartbeat usa `python -m overseer_agent` com env carregado no mesmo processo.

**Alterações:**
- `scripts/windows/_common.ps1`: `OverseerRepoRoot`, `Import-OverseerEnvFile`, `Write-OverseerEnvFile` (UTF-8 sem BOM), `Get-OverseerPython`.
- `provision-runners.ps1`: fix `RepoRoot`, exit em falha do Python.
- `heartbeat.ps1`, `Initialize-OverseerEnv.ps1`, `install-runner.ps1`, `register-infra-tasks.ps1`, `bootstrap-windows.ps1`, `ssh-tunnel.ps1`, `new-host-catalog.ps1`, `show-host-catalog.ps1`: alinhados com `_common.ps1`.
- `-PythonPath`, `-IdentityFile`, `-TaskUser` onde aplicável.
- `deploy/runners/WS1207.yaml`: catálogo Medidata para a máquina WS1207.

---

## [4.4.2] - 2026-06-08T12:35:00+01:00

### Catálogos Por Host (`deploy/runners/<host>.yaml`)

**Motivo:**
Diferenciar catálogos por máquina com nomes claros e eliminar paths fixos nos scripts; o provisionamento passa a resolver automaticamente o YAML correcto pelo hostname.

**Impacto:**
- Linux prod: `d4maia-pipelines.yaml` renomeado para `baze2.yaml`; `provision-runners.sh` sem `--catalog` encontra-o pelo hostname.
- Windows: catálogo `deploy/runners/<hostname>.yaml`; template Medidata em `_medidata.yaml` + `new-host-catalog.ps1`.
- Alterar YAML depois da migração: só `provision-runners --register`; Task Scheduler e crontab não se mexem.

**Alterações:**
- `scripts/provision_runners.py`: `resolve_runner_catalog()`, `--catalog` opcional, `--repo-root`.
- `deploy/runners/baze2.yaml`, `_example.yaml`, `_medidata.yaml`, `README.md`.
- `scripts/windows/show-host-catalog.ps1`, `new-host-catalog.ps1`; wrappers actualizados.
- `tests/test_provision_runner_catalog.py`.

---

## [4.4.1] - 2026-06-08T12:25:00+01:00

### Bootstrap Windows Com `.env.overseer` Automático

**Motivo:**
Reduzir o onboarding de uma máquina Windows a um único comando, gerando a configuração local (URL, host_id e token) sem edição manual e corrigindo o heartbeat agendado que não carregava a configuração.

**Impacto:**
`bootstrap-windows.ps1` instala o agente, cria o `.env.overseer` (URL do túnel, host_id pelo hostname, token via SSH do prod), regista o túnel SSH e o heartbeat, e arranca o túnel. O token nunca é versionado e o ficheiro fica com ACL restrita ao utilizador.

**Alterações:**
- `scripts/windows/Initialize-OverseerEnv.ps1`: gera o `.env.overseer` (idempotente, `-Force` para regravar, `-ApiToken` para override sem SSH).
- `scripts/windows/heartbeat.ps1`: wrapper que carrega o `.env.overseer` antes de `overseer-agent heartbeat`.
- `scripts/windows/bootstrap-windows.ps1`: onboarding completo num só comando.
- `scripts/windows/register-infra-tasks.ps1`: a tarefa de heartbeat passa a usar `heartbeat.ps1` (corrige falta de token/URL no heartbeat agendado).
- `scripts/windows/install-runner.ps1`: aceita `-SshTarget`/`-LocalPort` e, se presentes, gera o `.env.overseer` automaticamente.
- `templates/runner-windows/` e `docs/pipeline-integration.md`: fluxo simplificado com bootstrap único e configuração automática.

**Validação:**
- `python -m pytest -q` — testes Python existentes (alterações apenas em PowerShell/docs).

---

## [4.4.0] - 2026-06-08T12:10:00+01:00

### Runners Windows, Task Scheduler E Observabilidade Multi-host

**Motivo:**
Dar observabilidade completa e contínua a pipelines que correm em Windows (e em qualquer outro host), reportando ao Overseer central por túnel SSH, sem alterar o código dos pipelines e sem mudanças na API.

**Impacto:**
Cada máquina Windows liga-se à API central por túnel SSH em loopback (porta local `18090` -> `127.0.0.1:8090`), corre os pipelines via Task Scheduler com `run.ps1` e mantém heartbeats. Vários hosts podem reportar o mesmo pipeline lógico sem colidir, graças ao sufixo `__<host_id>` no `pipeline_id`.

**Alterações:**
- `templates/runner-windows/`: modelo de manifest, `run.ps1`, `.env.overseer` e README para máquinas Windows.
- `scripts/provision_runners.py`: agora cross-platform (`--platform linux|windows|auto`, `--host-id`), gera `run.ps1` ou `run.sh`, escreve metadata (`logical_id`, `host_id`, `os`) no manifest e o `catalog.json` para migração do agendador. Mantém compatibilidade com o fluxo Linux existente.
- `scripts/windows/`: `install-runner.ps1`, `ssh-tunnel.ps1`, `register-infra-tasks.ps1`, `provision-runners.ps1` e `migrate-taskscheduler.ps1`.
- `overseer_agent/__main__.py`: `heartbeat` passa a sondar `/v1/read/database` e a reportar `api_reachable` (estado `degraded` quando o túnel ou a API estão em baixo).
- `deploy/runners/windows-pipelines.yaml.example`: catálogo exemplo com `task_match` por pipeline.
- `docs/pipeline-integration.md` e `templates/runner/README.md`: secção Windows / Task Scheduler / multi-host.

**Validação:**
- `python -m pytest -q` — 18 testes.
- Provisionamento Windows e Linux validados localmente: manifests, wrappers e `catalog.json` gerados; compatibilidade do fluxo Linux (`run_sh`/`cron_match`) preservada.

---

## [4.3.1] - 2026-06-08T11:55:00+01:00

### Token Automático, Pipelines D4MAIA E Remoção Do Legado

**Motivo:**
Eliminar o campo manual de token na UI, migrar todos os pipelines D4MAIA do crontab para runners por manifest e remover o Overseer legado no servidor de produção.

**Alterações:**
- Frontend: token injectado via `js/overseer-config.js` no deploy; removidos inputs de token das páginas.
- `overseer-agent manifest --catalog-only` para registar DAG sem executar passos.
- Catálogo `deploy/runners/d4maia-pipelines.yaml` e scripts `provision-runners.sh`, `provision_runners.py`, `update-crontab-overseer.py`, `remove-legacy-overseer.sh`.
- Servidor `195.23.9.32`: 7 pipelines no crontab, legado arquivado, nginx `/apps/overseer/` removido, venv recriado em `~/overseer-py`.

**Validação:**
- `python -m pytest -q` — 18 testes.
- Runs manuais: 6/7 pipelines `ok`; `wireforms_sync` excedeu timeout de teste (10 min) — verificar na UI.

---

## [4.3.0] - 2026-06-08T10:12:15+01:00

### Runner Por Manifest E Deploy Em Docker + Nginx

**Motivo:**
Dar observabilidade por script sem alterar o código dos pipelines e preparar um caminho de deploy reprodutível com a API em Docker, o frontend em nginx e os pipelines ligados por crontab no servidor.

**Impacto:**
Passa a ser possível descrever um pipeline num manifest YAML externo ao repo e correr cada passo como um módulo no Overseer, com stdout/stderr e estado por passo. A primeira falha de um passo crítico interrompe a run. Em produção, a API corre isolada (sem MariaDB local), ligada ao schema `Overseer` do host, e o frontend é servido por nginx com proxy de `/v1`.

**Alterações:**
- `overseer_sdk/manifest_runner.py`: novo runner que lê manifests, regista o DAG linear e executa passos com telemetria por módulo.
- `overseer_agent/__main__.py`: novo comando `overseer-agent manifest <path> [--register-catalog] [--by]`.
- `overseer_sdk/__init__.py`: exporta `PipelineManifest`, `ManifestStep`, `load_manifest`, `register_catalog`, `run_manifest`.
- `templates/runner/`: modelo de manifest, wrapper `run.sh` e `.env.overseer` para uso em `~/overseer-runners/`.
- `docker-compose.prod.yml`: serviço único da API, bind em `127.0.0.1:8090`, `host.docker.internal` para a DB local.
- `deploy/nginx/overseer.conf` e `scripts/deploy-nginx-frontend.sh`: publicação do frontend em `/usr/share/nginx/html/Overseer` e proxy de `/v1`.
- `tests/test_manifest_runner.py`: cobertura do parsing, derivação do DAG e execução com sucesso/falha.

**Dependências:**
- Adicionada `PyYAML` em `requirements.txt` e `pyproject.toml` para leitura dos manifests.

**Ferramentas, MCP E Skills:**
- MCP servers: `user-time` para o carimbo temporal da entrada.
- Skills relevantes: `backend-architecture`, `cicd-pipeline-guardian`, `docker-coolify-deploy`, `ssh-server-ops`, `documentation-keeper`, `changelog-semver`, `definition-of-done`, `security-secrets-audit`.

**SSH / Servidores:**
- Deploy previsto em `eferreira@195.23.9.32`: backup do crontab, API em Docker ligada ao schema `Overseer` local, frontend em nginx e pipelines migrados para o runner por manifest. Acesso externo apenas via SSH.

**Ficheiros Removidos Ou Obsoletos:**
- N/A — apenas adições.

**Testes:**
- `python -m pytest -q` — passou com 18 testes.
- `docker compose -f docker-compose.prod.yml config` — válido.

**Validação:**
- Runner valida manifests e regista módulos por passo com mocks do `OverseerClient`.
- Compose de produção gera configuração com a API em loopback e `host.docker.internal`.

**Refs:**
- Pedido do utilizador: observabilidade por script sem estragar o código dos pipelines e deploy Docker/nginx no servidor.

**Diff:**
Adiciona runner por manifest, comando CLI, template de runner, compose de produção e publicação do frontend em nginx.

---

## [4.2.1] - 2026-06-05T16:11:31+01:00

### Template Frontend Ligado A Dados Reais

**Motivo:**
Adaptar o template colocado em `frontend/` para mostrar dados reais do Overseer, mantendo o visual do template.

**Impacto:**
As vistas `dashboard`, `runs`, `DAG` e `ambiente` passam a preencher KPIs, tabelas, timeline, canvas e atividade com dados de `/v1/read/*`. A página inicial continua sem launcher: `index.html` redireciona para `dashboard.html`.

**Alterações:**
- `frontend/dashboard.html`, `run-detail.html`, `lineage.html`, `deployments.html`: adicionados pontos `data-*` ao template para renderização dinâmica.
- `frontend/js/app.js`: substituída lógica estática por fetch aos endpoints do Overseer, token opcional em `sessionStorage`, estados vazios, erro, filtros, tabs e copy.
- `frontend/css/app.css`: adicionados estilos mínimos para alertas, estados vazios e input de token.
- `frontend/index.html`: mantido redirecionamento para `dashboard.html`.

**Dependências:**
- N/A — não foram adicionadas dependências.

**Ferramentas, MCP E Skills:**
- MCP servers: N/A — não há configuração MCP de projeto.
- Skills usadas: `frontend-architecture`, `fullstack-delivery`, `documentation-keeper`, `changelog-semver`, `definition-of-done`, `security-secrets-audit`, `prompt-injection-guard`.

**SSH / Servidores:**
- N/A — nenhum SSH, servidor remoto ou produção foi acedido.

**Ficheiros Removidos Ou Obsoletos:**
- N/A — ficheiros de template extra foram preservados como fornecidos pelo utilizador, mas não são usados como entrada inicial.

**Testes:**
- `python -m pytest -q` — passou com 10 testes e 1 aviso de depreciação do TestClient.
- `node --check frontend\js\app.js` — passou.
- `docker compose build` — passou.
- `docker compose up -d` — passou.

**Validação:**
- `/ui/dashboard.html`, `/ui/run-detail.html`, `/ui/lineage.html` e `/ui/deployments.html` responderam 200.
- `/ui/js/app.js` respondeu 200.
- `/v1/read/overview` e `/v1/read/database` responderam com dados reais.

**Refs:**
- Pedido do utilizador: adaptar os dados ao template colocado na pasta `frontend`.

**Diff:**
Frontend preserva o template visual e passa a renderizar os dados reais do Overseer.

---

## [4.2.0] - 2026-06-05T15:53:35+01:00

### Observabilidade DAG Por API E Frontend Estático

**Motivo:**
Separar o Overseer do código dos pipelines reais, remover exemplos de negócio do núcleo e transformar o produto num observador de DAGs alimentado por API.

**Impacto:**
O Overseer deixa de executar pipelines por subprocesso local. O contrato principal passa a ser registo de catálogo por `/v1/catalog/pipelines` e telemetria por `/v1/events/*`. A UI abre diretamente no dashboard, lê dados reais da FastAPI e o Docker deixa de precisar de Node/Vite.

**Alterações:**
- `src/overseer_core/store.py`: adicionadas tabelas `overseer_pipeline_nodes` e `overseer_pipeline_edges`, upsert de catálogo DAG, leitura de DAG e remoção da execução por subprocesso.
- `src/overseer_api/routers/catalog.py`: criado `POST /v1/catalog/pipelines`.
- `src/overseer_api/routers/read.py`: criado `GET /v1/read/pipelines/{pipeline_id}/dag`.
- `src/overseer_api/routers/orchestrate.py`: removido endpoint de execução local de pipelines.
- `src/overseer_api/main.py`: frontend passa a ser servido de `frontend/`; `/` e `/ui` redirecionam para `/ui/dashboard.html`.
- `frontend/`: removido launcher/landing BruinOps e criada UI estática Overseer ligada a `/v1/read/*`.
- `overseer_sdk/client.py`: adicionado método `register_pipeline`.
- `overseer_agent/__main__.py`: removido comando `run` que chamava o endpoint removido.
- `scripts/overseer_emit_demo.py`: demo passa a registar um DAG genérico e emitir eventos sobre esse catálogo.
- `Dockerfile` e `docker-compose.yml`: removido build Node/Vite e mount de `pipelines/`.
- `templates/pipeline-repo/` e `docs/pipeline-integration.md`: template e documentação passam a usar registo DAG por API.
- `README.md`, `PROJECT_CONTEXT.md`, `docs/adr/0001-overseer-core-api-refactor.md`, `openapi/overseer-api.yaml` e `tasks/todo.md`: documentação alinhada com o contrato 4.2.0.

**Dependências:**
- `requirements.txt`: removidas dependências de pipeline/YAML não usadas pelo núcleo.
- `pyproject.toml`: versão atualizada para 4.2.0 e dependências do SDK explicitadas.

**Ferramentas, MCP E Skills:**
- MCP servers: N/A — não há configuração MCP de projeto.
- Skills usadas: `repo-onboarding`, `skill-selector`, `backend-architecture`, `frontend-architecture`, `fullstack-delivery`, `api-contract-guardian`, `database-migration-safety`, `dependency-manager`, `file-pruner`, `documentation-keeper`, `handoff-maintainer`, `changelog-semver`, `definition-of-done`, `security-secrets-audit`, `prompt-injection-guard`, `stop-the-slop`.
- Fallbacks: comandos locais foram executados com aprovação por erro inicial do sandbox Windows.

**SSH / Servidores:**
- N/A — nenhum SSH, servidor remoto ou produção foi acedido.

**Ficheiros Removidos Ou Obsoletos:**
- Removidos `frontend/landing.html`, `frontend/bruinops-prototype.html` e o conteúdo versionado de `pipelines/microsoft_forms_2_datalake/`.
- Removido `templates/pipeline-repo/pipeline.yaml` como contrato obrigatório.
- Mantidos templates genéricos de integração por API.

**Testes:**
- `python -m pytest -q` — passou com 10 testes e 1 aviso de depreciação do TestClient.
- `docker compose config` — passou.
- `docker compose build` — passou.
- `docker compose up -d` — passou.
- `docker compose exec -T overseer-api python scripts/overseer_emit_demo.py` — registou DAG demo e run.

**Validação:**
- Testes de contrato cobrem registo DAG, leitura DAG, eventos de módulo, redirecionamento da UI e remoção do endpoint de execução local.
- `GET /v1/health` e `GET /ui/dashboard.html` responderam 200.
- `GET /` respondeu 307 para `/ui/dashboard.html`.
- `GET /v1/read/pipelines/demo_dag/dag` confirmou 3 nodes e 2 edges.

**Refs:**
- Pedido do utilizador: implementar o plano “Overseer Como Observador De DAGs”.

**Diff:**
Overseer 4.2.0 passa a ser um observador de DAGs desacoplado dos pipelines reais, com frontend estático ligado à API e Docker simplificado.

---

## [4.1.0] - 2026-06-04T19:08:22+01:00

### DB Oficial, Kit De Pipelines E Frontend Operacional

**Motivo:**
Permitir ligar o Overseer ao schema oficial `Overseer`, mostrar dados reais a fluir no frontend e definir uma forma única de instrumentar todos os repositórios de pipelines.

**Impacto:**
O Compose passa a aceitar `OVERSEER_DB_URL` para apontar para uma DB oficial externa, mantendo fallback local. A UI mostra o estado da DB, contagens por tabela, lanes de runs, DAGs, triggers, heartbeats, logs e detalhe de módulos. Os repos de pipelines passam a ter um template padrão e uma dependência instalável `overseer-core`.

**Alterações:**
- `src/overseer_core/store.py`: adicionada leitura segura de estado da DB, URL mascarada, contagens por tabela e suporte a `/app/host_pipelines` sem sobrepor `/app/pipelines`.
- `src/overseer_api/routers/read.py`: adicionado `GET /v1/read/database`.
- `docker-compose.yml`: `OVERSEER_DB_URL` passa a ser configurável por `.env`; pipelines do host montam em `/app/host_pipelines:ro`.
- `.env.example` e `.env.official.example`: documentada configuração local e oficial sem segredos reais.
- `pyproject.toml`: criado pacote instalável `overseer-core` com script `overseer-agent`.
- `templates/pipeline-repo/`: criado kit padrão para cada repo de pipeline.
- `docs/pipeline-integration.md`: documentado contrato único de instrumentação por API.
- `scripts/overseer_emit_demo.py`: criado emissor de run/módulos/logs/heartbeat para validar fluxo no schema ativo.
- `webapp/src/main.jsx` e `webapp/src/styles.css`: frontend refeito como consola operacional densa inspirada em Airflow/Bruin Monitor SaaS.
- `openapi/overseer-api.yaml`, `README.md`, `PROJECT_CONTEXT.md`, `tasks/todo.md`: documentação atualizada.

**Dependências:**
- `pyproject.toml` adicionado com dependências Python instaláveis.
- `webapp/package.json` e `webapp/package-lock.json` atualizados para versão 4.1.0.

**Ferramentas, MCP E Skills:**
- MCP servers: N/A — não há configuração MCP de projeto.
- Skills usadas: `fullstack-delivery`, `frontend-architecture`, `backend-architecture`, `database-migration-safety`, `api-contract-guardian`, `dependency-manager`, `security-secrets-audit`, `documentation-keeper`, `handoff-maintainer`, `changelog-semver`, `definition-of-done`, `stop-the-slop`.
- Fallbacks: Browser MCP indisponível na sessão; validação frontend feita por build Vite e HTTP de HTML/assets.

**SSH / Servidores:**
- N/A — nenhum servidor ou SSH foi acedido. A DB oficial fica preparada por `.env`, mas credenciais reais não existem no repo.

**Ficheiros Removidos Ou Obsoletos:**
- N/A — não houve nova remoção relevante nesta etapa.

**Testes:**
- `python -m pytest -q` — passou com 5 testes.
- `docker compose config` — passou.
- `docker compose build` — passou.
- `docker compose up -d` — passou.
- `docker compose exec -T overseer-api python scripts/overseer_emit_demo.py` — criou run de demonstração.

**Validação:**
- `/v1/read/database` confirmou DB `Overseer`, modo `docker-local`, URL mascarada e contagens `pipelines=1`, `runs=1`, `modules=3`, `logs=3`, `heartbeats=1`.
- `/v1/read/overview` confirmou pipeline `microsoft_forms_2_datalake` e run demo `ok`.
- `/ui/` serviu HTML com assets em `/ui/assets/...`; JS e CSS responderam 200.
- Auditoria literal não encontrou valores antigos sensíveis conhecidos.

**Refs:**
- Pedido do utilizador: ligar ao schema Overseer oficial, preparar integração padrão nos repos de pipelines e melhorar frontend para algo entre Airflow e Bruin Monitor SaaS.

**Diff:**
Overseer ganha camada operacional 4.1.0: DB oficial por configuração, kit de adoção para pipelines, endpoint de estado da DB, demo de fluxo e frontend de monitorização mais rico.

---

## [4.0.0] - 2026-06-04T11:42:09+01:00

### Refactor Core API, Docker E Frontend Local

**Motivo:**
Simplificar agressivamente o Overseer e transformá-lo num núcleo operacional com API de leitura, API de escrita, API de orquestração, frontend local moderno e execução Docker reproduzível em qualquer sistema operativo com Docker.

**Impacto:**
Quebra compatibilidade com o fluxo antigo `DB -> JSON -> frontend externo`, scheduler CLI legado e schema antigo. O contrato suportado passa a ser HTTP/API token, tabelas `overseer_*`, SDK/CLI para pipelines e dashboard React/Vite servido pela FastAPI. O fluxo recomendado de arranque é Docker-first e não requer Python ou Node instalados no host.

**Alterações:**
- `src/overseer_core/store.py`: criado store SQLAlchemy com schema novo para pipelines, runs, módulos, logs, heartbeats e triggers.
- `src/overseer_api/main.py`: refeito para FastAPI v4 com lifespan, health, leitura, eventos e orquestração.
- `src/overseer_api/routers/read.py`, `events.py`, `orchestrate.py`, `health.py`: adicionados/substituídos routers canónicos.
- `overseer_sdk/client.py` e `overseer_agent/__main__.py`: adicionados SDK Python e CLI wrapper para registar telemetria, heartbeats, triggers e execuções.
- `overseer_monitor/monitor.py`: adaptado para escrever via API mantendo compatibilidade razoável com pipelines existentes.
- `webapp/`: substituído frontend legado por React/Vite com dashboard local, detalhe de runs, logs, módulos e ações operacionais.
- `webapp/package.json`: build Vite configurado com `--base=/ui/` para os assets serem servidos corretamente quando a app está montada em `/ui/`.
- `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `scripts/overseer-up.ps1`, `scripts/overseer-up.sh`, `overseer-up.cmd`: implementado fluxo Docker multi-plataforma por comando simples.
- `openapi/overseer-api.yaml`: contrato OpenAPI atualizado para os endpoints v4.
- `README.md`, `PROJECT_CONTEXT.md`, `tasks/todo.md`, `skills/overseer-pipeline/SKILL.md`: documentação e Skill local alinhadas com o novo contrato.
- `docs/adr/0001-overseer-core-api-refactor.md`: ADR criada para a decisão arquitetural.
- `pipelines/microsoft_forms_2_datalake/`: mantido como único exemplo e atualizado para apontar para o frontend local.
- `pipelines/microsoft_forms_2_datalake/secrets/database.json.example.json`: valores com aparência de credencial substituídos por placeholders.
- `overseer_sdk/runtime_context.py`: removido host/IP antigo por defeito; deteção local passa a depender de `OVERSEER_DB_LOCAL_HOSTS`.

**Dependências:**
- `webapp/package.json` e `webapp/package-lock.json` adicionados com versões fixas para React, Vite, TypeScript e `lucide-react`.
- `requirements.txt` mantido como manifesto Python para a API e exemplo de pipeline.
- Docker passa a instalar dependências Python e Node dentro da imagem, evitando instalação manual no host.

**Ferramentas, MCP E Skills:**
- MCP servers: N/A — não foram encontradas configurações `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json` ou `.claude/mcp.json`.
- Skills usadas: `repo-onboarding`, `skill-selector`, `backend-architecture`, `frontend-architecture`, `fullstack-delivery`, `api-contract-guardian`, `database-migration-safety`, `dependency-manager`, `file-pruner`, `security-secrets-audit`, `prompt-injection-guard`, `documentation-keeper`, `handoff-maintainer`, `changelog-semver`, `definition-of-done`, `stop-the-slop`.
- Fallbacks: ferramentas locais e Docker; não houve MCP de projeto disponível.

**SSH / Servidores:**
- N/A — nenhum servidor, SSH, deploy remoto ou produção foi acedido.

**Ficheiros Removidos Ou Obsoletos:**
- Removidos: `orchestrator.py`, `src/pm_runtime/`, routers/builders legados, `src/overseer_api/routers/runners.py`, migrations antigas, export JSON, scripts cron/Slack antigos, `pipelines/_template/`, `pipelines/webapp_medidata/`, frontend JS/CSS legado e documentação MAIATRON/PRD fora de contrato.
- Mantido: `pipelines/microsoft_forms_2_datalake/` como exemplo funcional.
- Observação: `PROJECT_CONTEXT.template.md` já aparecia removido antes desta tarefa e essa remoção foi preservada.

**Testes:**
- `python -m pytest -q` — passou com 4 testes.
- `docker compose build` — passou; validou `npm ci`, `vite build` e instalação Python dentro do container.
- `docker compose up -d` — executado para aplicar a correção do frontend no container local.
- `Invoke-WebRequest http://127.0.0.1:8090/ui/` — passou; HTML referencia `/ui/assets/...`.
- `Invoke-WebRequest http://127.0.0.1:8090/ui/assets/...` — passou para JS e CSS.
- `npm install` local em Windows/OneDrive — falhou por permissões em `webapp/node_modules`; sem impacto no fluxo suportado, porque Docker faz a instalação dentro da imagem e `.dockerignore` exclui `node_modules`.

**Validação:**
- Estado Git verificado antes e durante a tarefa.
- OpenAPI, README, PROJECT_CONTEXT, ADR, Skill local e scripts de arranque alinhados com o novo contrato.
- Pesquisa por referências legadas confirmou que MAIATRON/JSON ficam apenas em contexto de remoção no plano/ADR/changelog.
- Auditoria de segredos substituiu um exemplo com aparência de credencial e removeu infraestrutura antiga embutida; se o valor original tiver sido real ou reutilizado, deve ser rodado no sistema de origem.
- Build Docker multi-stage confirma que o arranque é reprodutível em ambientes com Docker.

**Refs:**
- Pedido do utilizador: refactor geral do Overseer, duas APIs nucleares, API separada de orquestração, frontend React/Vite, schema novo, remover legado e Docker instalável em qualquer sistema operativo.

**Diff:**
Overseer passa de runtime legado com export externo para aplicação fullstack local Docker-first, API-first e preparada para MariaDB/MySQL ou outro dialecto SQLAlchemy.

---

## [2.4.2] - 2026-06-03T12:46:28+01:00

### Atualização De Documentação Operacional E Segurança

**Motivo:**
Aplicar as regras de `AGENTS.md` ao repositório, criar contexto específico do projeto e corrigir exposição de credencial em documentação.

**Impacto:**
Melhora a continuidade operacional para agentes e humanos, documenta arquitetura/estrutura real, clarifica ausência de MCP/Docker configurados e remove do README uma credencial com aparência real. Se essa credencial for válida ou reutilizada, continua a ser necessária rotação no sistema de origem.

**Alterações:**
- `README.md`: reescrito com badges, arquitetura Mermaid, estrutura real, instalação, comandos principais, segurança, Docker avaliado, troubleshooting e referências operacionais.
- `PROJECT_CONTEXT.md`: criado com contexto confirmado do projeto, stack, fluxos, MCP, Skills, Git, Docker, riscos e comandos principais.
- `tasks/todo.md`: atualizado com plano, validação e revisão final da tarefa.
- `HANDOFF.md`: atualizado com estado final, bloqueios, validações, Skills/MCP, Git e risco de segurança.
- `CHANGELOG.md`: adicionada esta entrada.

**Dependências:**
- N/A — `requirements.txt` foi validado, mas não alterado.

**Ferramentas, MCP E Skills:**
- MCP servers: N/A — não foram encontradas configurações `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json` ou `.claude/mcp.json`.
- Skills usadas: `repo-onboarding`, `skill-selector`, `safe-git-operator`, `security-secrets-audit`, `prompt-injection-guard`, `dependency-manager`, `file-pruner`, `documentation-keeper`, `handoff-maintainer`, `changelog-semver`, `definition-of-done`, `stop-the-slop`.
- Fallbacks: executor PowerShell em sandbox falhou; comandos necessários foram executados com escalamento aprovado.

**SSH / Servidores:**
- N/A — nenhum servidor ou SSH foi acedido.

**Ficheiros Removidos Ou Obsoletos:**
- Removidos: diretórios `__pycache__` gerados por `compileall` nesta sessão.
- Candidatos: `docs/Guia_Producao_Step_by_Step.rtf` pode ser duplicado do guia Markdown, mas foi mantido por poder ter valor histórico.

**Testes:**
- `python -m compileall orchestrator.py overseer_monitor overseer_sdk scripts src pipelines` — passou.
- `python orchestrator.py --help` — falhou por `ModuleNotFoundError: No module named 'yaml'`; instalar `requirements.txt` antes de validar CLI completo.

**Validação:**
- Estado Git verificado.
- Skills e MCP verificados.
- `README.md` verificado para confirmar remoção da credencial documentada.
- Documentação revista para evitar tecnologia, deploy, licença, CI/CD ou testes não confirmados.

**Refs:**
- Pedido do utilizador: "Lê o AGENTS.md e atualiza tudo e segue todas as instruções neste repo".

**Diff:**
Documentação operacional criada/atualizada, README endurecido contra exposição de segredos e handoff/changelog alinhados com a política do repositório.

---

## [2.4.1] - 2026-03-31

### Changed
- **Runtime sync from MAIATRON**: `index.production.html`, `overseer.production.js`, `overseer.live.js`, `overseer.css` synced from canonical `MAIATRON/apps/overseer/*` source.
- **Frontend overhaul (via MAIATRON)**: dead v1 JS code removed (6 duplicate functions), ~400 lines dead CSS removed (kiosk, header v2.1/v2.4, catalog, duplicates), design gaps fixed (severity pills light theme, lineage tile border, schedule input).
- **New frontend features (via MAIATRON)**: CSV export for runs, advanced filters (date range, owner, criticality), retry run with RBAC, real-time toast on status change, pipeline health check grid in dashboard.

### AI Context Delta
- Runtime files are now in sync with MAIATRON v6.1.2 Overseer frontend; all dead code from v1/v2 function shadowing is resolved.
- `ov_ensure_governance_schema()` removed from per-request API path; run `php backend/apps/overseer/migrate.php` at deploy time instead.
- New deploy artifact: `backend/apps/overseer/migrate.php` — idempotent CLI-only schema migration.

## [2.4.0] - 2025-07-16

### Changed
- **Pipeline standardization**: all pipelines now follow the same canonical pattern — `OverseerMonitor` (standalone), `LineageEmitter` (orchestrator), `SlackNotifier` (mandatory), `RuntimeContext` (portability).
- **Template rewrite**: `pipelines/_template/src/main.py` rewritten with `PipelineOrchestrator` class pattern, full documentation in `pipelines/_template/README.md`.
- **forms_2_datalake migration**: removed local `overseer_monitor.py` and `overseer_frontend.py`; pipeline now imports shared `OverseerMonitor` from `overseer_monitor/` package.
- **webapp_medidata**: added `OverseerMonitor` standalone tracking so runs outside orchestrator are properly recorded in `pipeline_runs`.
- **example_pipeline**: rewritten from stub (`print("ok")`) to full canonical pattern with monitor, lineage, and Slack.
- **entrypoint_windows**: added to all `pipeline.yaml` files for cross-platform portability.
- **monitoring.json.example**: updated to canonical field names (`logs_table`, `script_name`).

### Removed
- `pipelines/microsoft_forms_2_datalake/src/overseer_monitor.py` (local copy, replaced by shared module)
- `pipelines/microsoft_forms_2_datalake/src/overseer_frontend.py` (legacy HTTP server, replaced by MAIATRON api.php)

### AI Context Delta
- All pipelines use the shared `overseer_monitor.OverseerMonitor` — no local copies.
- `OverseerMonitor.finish()` takes `context` dict (`pipeline_id`, `trigger_type`, `owner`, `criticality`), not `db_manager`.
- `monitor.start()` is called only when `not runtime_ctx.orchestrator_managed`.
- Pipeline constants: `PIPELINE_ID`, `PIPELINE_OWNER`, `PIPELINE_CRITICALITY` must match `pipeline.yaml`.
- `entrypoint_windows` added to YAML contract for Windows portability.

## [2.3.6] - 2026-03-31

### Fixed
- **Medidata schema alignment on `baze2`**: documentado e reposto o alinhamento operacional para `webapp_medidata`, deixando explícito que a app MAIATRON publicada lê `medidata_scrape_runs` e `medidata_indicator_records_raw` no schema `MAIATRON` e não no schema `Overseer`.

### AI Context Delta
- `pipelines/webapp_medidata/secrets/database.json -> database.database` deve apontar para `MAIATRON` para que o scraping alimente a app publicada em `baze2`.

## [2.3.5] - 2026-03-31

### Fixed
- **Export resiliente quando `pipeline_script_logs` falha**: `persist_pipeline_script_logs()` deixou de abortar o export quando uma entrada tem `scriptLogMessage = null` durante o fallback após erro de escrita na BD; o export continua a degradar para file logging e preserva a geração de `frontend/pm_payload.json` e `frontend/pm_details.json`.

### AI Context Delta
- Fallback de `persist_pipeline_script_logs()` normaliza `scriptLogMessage` com `str(... or "")` antes de truncar, evitando `TypeError` no handler de erro.

## [2.3.4] - 2026-03-05

### Fixed
- **Rollback visual completo do runtime**: `runtime/index.production.html`, `runtime/overseer.css`, `runtime/overseer.production.js` e `runtime/overseer.live.js` foram repostos a partir da baseline oficial `Frontends/MAIATRON/apps/overseer`, removendo alterações de estilo feitas no Overseer.

### Changed
- **Guardrail operacional**: `python orchestrator.py deploy-frontend` passou a estar bloqueado por política MAIATRON e termina com erro controlado (`exit code 2`) sem copiar HTML/JS/CSS.
- **Contrato de operação reforçado**: Overseer mantém apenas o fluxo de dados (`DB -> JSON -> frontend`), sem ownership de UI/estilo.
- **Lineage + Slack preservados**: sem regressão nas regras recentes (`module_lineage` por última run e canal Slack `overseer` unificado).

### AI Context Delta
- `cmd_deploy_frontend()` deixou de fazer deploy local/SSH de assets e agora apenas imprime instrução para usar `python scripts/export_payload_from_db.py`.
- Ajuda CLI de `deploy-frontend` indica explicitamente que o comando está bloqueado por política.
- Baseline visual do runtime deve seguir sempre `Frontends/MAIATRON/apps/overseer`.

## [2.3.3] - 2026-03-05

### Fixed
- **Lineage com módulos legados misturados**: `load_module_lineage()` no export passou a construir `module_lineage` e `pipeline_scripts` apenas com eventos da última run por pipeline, eliminando ruído histórico (ex.: módulos antigos em `webapp_medidata`).

### Changed
- **Selection boxes MAIATRON unificadas**: todos os `<select>` no frontend runtime receberam classe/estilo uniforme (`maiatron-select`) com espaçamento consistente entre filtros, headers, paginação e Orquestração.
- `renderAll()` e `initUi()` aplicam `applyMaitronSelectClasses()` para garantir consistência visual em selects renderizadas dinamicamente.
- `overseer.production.js` sincronizado com `overseer.live.js`.
- Cache-buster atualizado para `v2.3.3-ui-lineage-slack` em `runtime/index.production.html`.
- **Slack unificado**: `secrets/slack.json` e `pipelines/webapp_medidata/secrets/slack.json` alinhados com `pipelines/microsoft_forms_2_datalake/secrets/slack.json` (canal `overseer` + mesmo webhook).

### AI Context Delta
- `module_lineage` agora é "latest-run scoped" por pipeline; `run_trigger_info` continua por run (`pm_details.trigger_info` não mudou de contrato).
- Novo helper frontend: `applyMaitronSelectClasses(scope=document)` adiciona `.maiatron-select` a todos os `<select>` em `initUi()` e após `renderAll()`.
- Estilo de selects consolidado em `runtime/overseer.css` com foco, ícone de dropdown, contraste light/dark e espaçamento uniforme em `.chart-header`, `.filters`, `.pager`, `.schedule-cell` e `.schedule-input`.

## [2.3.2] - 2026-02-24

### Fixed
- **Refresh button not resetting countdown**: Clicking the refresh button now resets the 30s auto-refresh timer (stops → refreshes → restarts). Added `manualRefresh()` wrapper with loading indicator on the button during fetch.
- **Pause/schedule mutations lost on auto-refresh**: `buildModelFromPayload()` unconditionally replaced `state.orchestratorPipelines` from backend payload, overwriting local pause/schedule changes every 30s. Fix: introduced `state.pendingScheduleMutations` — mutations are recorded with timestamp and reapplied via `rehydratePendingScheduleMutations()` after each payload rebuild. Entries auto-expire after 3 minutes or when backend confirms the change.
- **MAIATRON logo CSS discrepancies**: Early CSS rules (`.logo-img` filter, `.logo-ring` 8s spin, `.brand-logo::before`, `.brand-img` filter, `.brand-ring` 8s spin) conflicted with the harmonization v1.6 block. Removed dead/broken rules including invalid `filter: brightness(1) saturate(1) none` in light theme. Logo now renders identically to other MAIATRON apps.

### Removed
- **"Timeline da Run" section**: Removed redundant card-based timeline (`renderOrchestratorEvents()`, `deriveOrchestratorEvents()`, `state.orchEvents`, HTML `<article>` block). It was a 1:1 transform of the runs table data with zero additional information. "Runs de Orquestracao" table is the single source of truth.

### Changed
- `initUi()`: `refreshBtn` now calls `manualRefresh()` instead of `refreshAllData()`.
- `handleScheduleChange()`: Records mutation in `state.pendingScheduleMutations`.
- `handlePauseToggle()`: Records mutation with `prev_schedule` in `state.pendingScheduleMutations`.
- `buildModelFromPayload()`: Calls `rehydratePendingScheduleMutations()` after rebuilding `orchestratorPipelines`.
- `renderAll()`: No longer calls `renderOrchestratorEvents()`.
- `handleOrchestratorAction()`: No longer calls `deriveOrchestratorEvents()` or `renderOrchestratorEvents()`.
- `orchRefreshBtn` handler: No longer calls `renderOrchestratorEvents()`.
- Removed `@keyframes spin` (dead — replaced by `@keyframes maiatronRingSpin`).
- Removed early `.brand-ring` and `.logo-ring` rules (overridden by harmonization `!important`).
- Cache-buster bumped to `v2.3.2-polish`.
- `overseer.production.js` synced with `overseer.live.js`.

### AI Context Delta
- **Pending schedule mutations**: `state.pendingScheduleMutations` is a `{[pipelineId]: {schedule, prev_schedule, ts}}` map. Recorded in `handleScheduleChange()` and `handlePauseToggle()`. Rehydrated in `rehydratePendingScheduleMutations()` which runs at the end of `buildModelFromPayload()`. Entries expire after 3 min or when backend agrees.
- **Manual refresh**: `manualRefresh()` wraps `stopAutoRefresh() → refreshAllData() → startAutoRefresh()`. Adds `.loading` class to `#refreshBtn` during fetch.
- **Timeline removed**: `orchEvents` state key removed. `deriveOrchestratorEvents()` and `renderOrchestratorEvents()` functions deleted. `#orchEventsList` HTML element removed from `index.production.html`.
- **CSS cleanup**: Early `.logo-img` filter, `.logo-ring`, `@keyframes spin`, `.brand-logo::before`, `.brand-img` filter/z-index, `.brand-ring`, and broken light-theme filter rules removed. Only structural properties (width/height/object-fit) kept where needed. Harmonization v1.6 block (L2700+) is now the single authority for logo/ring/brand styling.

## [2.3.1] - 2026-02-24

### Fixed
- **Running indicator never showing (Bug 1)**: The green pulsating dot never appeared because `cmd_export()` only ran after `execute_pipeline()` finalized the status — the brief "running" window was never captured in the JSON payload. Fix: introduced **client-side inflight tracking** (`overseer_inflight_v1` localStorage key). When the user clicks "Run Now", the pipeline is added to the inflight store; `buildModelFromPayload()` adds inflight entries to `state.runningPipelines` until the DB confirms a terminal status or a 30-minute timeout expires.
- **Pause not surviving browser refresh (Bug 2)**: `consume_schedule_triggers()` ran at step 8 in the scheduler loop, after the 15-min export check at step 2 — no re-export happened after YAML rewrite. Fix: scheduler now captures the return value of `consume_schedule_triggers()` and submits an immediate export when `> 0` triggers were processed.
- **Orch runs table duplicated and cluttered (Bug 3)**: `state.orchRuns` merged 3 sources (DB runs, DB triggers-as-runs, localStorage) with incompatible ID types, causing dedup to fail — same action appeared 2-3 times. Fix: removed `normalizeTriggerAsRun()` from the merge; `orchRuns` is now built from `dbRuns + inflightRows` only. Table simplified to 4 columns (Pipeline, Status, Criado em, Origem) — removed ID column (opaque UUIDs/ints) and Acoes column (redundant "Eventos" button).

### Added
- `loadInflight()` / `saveInflight()` / `addInflight()` / `pruneInflight()` JS helpers for client-side inflight pipeline tracking.

### Changed
- `handleOrchestratorAction()`: After trigger delivery, calls `addInflight()` and immediately adds pipeline to `state.runningPipelines` + re-renders schedules table (shows dot).
- `buildModelFromPayload()`: Uses `pruneInflight(dbRuns)` to reconcile inflight entries against DB, adds surviving entries to `runningPipelines`.
- `renderOrchestratorRuns()`: 4-column layout (Pipeline, Status, Criado em, Origem); removed ID and Acoes columns.
- `deriveOrchestratorEvents()`: Source label simplified from `frontend-cli-copy` to `cli-copy`.
- Scheduler step 8: Captures `consume_schedule_triggers()` return, forces immediate export if > 0.
- Cache-buster bumped to `v2.3.1-inflight-dedup`.
- `overseer.production.js` synced with `overseer.live.js`.

### AI Context Delta
- **Inflight tracking**: `overseer_inflight_v1` localStorage stores `[{pipelineId, triggerId, startedAt}]`. Entries are pruned in `buildModelFromPayload()` when a matching DB run with terminal status appears, or after 30 min timeout. Inflight entries are shown as "running" rows in orchRuns and activate the green dot.
- **Orch runs merge**: No longer mixes `orchestrator_triggers` as pseudo-runs. Only `orchestrator_runs_local` (DB) + inflight entries (localStorage) are merged. `loadTriggerHistory()` still exists for backwards compat but is no longer mixed into `orchRuns`.
- **Forced export after schedule change**: Scheduler step 8 now triggers an immediate `export_payload_from_db.py` run when schedule triggers are consumed, so the frontend picks up `schedule: "paused"` on next 30s refresh.

## [2.3.0] - 2026-02-24

### Added
- **Pause/Resume schedule button**: Pipeline catalog table now shows a **Pause** button for scheduled pipelines and a **Resume** button when paused. Uses `schedule: "paused"` in the YAML (reuses the existing `writeScheduleTrigger → trigger.php → consume_schedule_triggers → cmd_schedule_set` flow). Previous cron expression saved as `prev_schedule` in the YAML for persistence across browsers.
- **Live running indicator**: Green pulsating dot appears next to the pipeline name in the catalog table when a pipeline has an active run with `status: "running"` in `orchestrator_runs`. Also added a dedicated `status-running` CSS class (blue pill) in the Runs de Orquestracao table.
- **`handlePauseToggle()` JS function**: Manages pause/resume logic — stores `prev_schedule` locally in `pipeline_catalog` entry and sends schedule change trigger.

### Changed
- `cmd_schedule_set()`: Now accepts `"paused"` as a valid schedule value. Saves `prev_schedule` in YAML when pausing, removes it when resuming.
- Scheduler daemon: Skips pipelines with `schedule: "paused"` (same as `"manual"`).
- `consume_schedule_triggers()`: Accepts `"paused"` in cron validation whitelist.
- `load_pipeline_catalog()` in export: Includes `prev_schedule` field from YAML.
- `isValidCron()` JS: Accepts `"paused"` as valid.
- `orchestratorStatusClass()` JS: Returns `status-running` for running status.
- Cache-buster bumped to `v2.3.0-pause-running`.
- `overseer.production.js` synced with `overseer.live.js`.

### AI Context Delta
- `schedule: "paused"` is a reserved YAML value like `"manual"`. Scheduler skips it. When set, `prev_schedule` holds the original cron.
- Running indicator: reads `state.payload.orchestrator_runs` (already exported) and builds `state.runningPipelines = new Set()` of pipeline IDs with `status === "running"`.
- Pause flow: frontend sends `type: "schedule_change"` trigger with `new_schedule: "paused"` → same PHP/SFTP/consume path → `cmd_schedule_set()` saves `prev_schedule` in YAML.
- Resume flow: frontend reads `prev_schedule` from `pipeline_catalog` export, sends the cron as `new_schedule` → `cmd_schedule_set()` removes `prev_schedule` from YAML.

## [2.2.2] - 2026-02-24

### Fixed
- **Run Now stuck at "queued" (definitive fix)**: `consume_file_triggers()` was processing trigger files but never writing the result back to `orchestrator_triggers_local` DB table. The frontend only saw the localStorage "queued" entry because no DB record existed to supersede it. Now `_persist_file_trigger()` inserts/upserts the final status (`consumed`/`failed`) into the DB, so the next payload export includes the trigger with correct status and dedup removes the stale localStorage entry.
- **Duplicate DB records**: Orchestrator's `OverseerMonitor.finish()` and the pipeline's own `OverseerMonitor.finish()` both wrote to `pipeline_runs`. Now the orchestrator injects `OVERSEER_ORCHESTRATOR_MANAGED=1` env var into the subprocess, and the pipeline skips its own DB write when that env var is set.
- **trigger_type hardcoded as "manual"**: `run_step()` context now uses the actual `trigger_source` value (`manual`, `trigger_file`, `trigger_db`, `schedule`) instead of hardcoded `"manual"`.

### Added
- **`triggerType` column**: Auto-migrated via `ensure_tables()` on `pipeline_runs`. Tracks whether a run was `manual`, `trigger_file`, `trigger_db`, or `schedule`.
- **`triggerType` in export**: `RunRecord`, SQL queries, `to_run_summary()`, and export `fields` list now include `triggerType`.
- **`deploy-frontend` command**: `python orchestrator.py deploy-frontend` copies `overseer.production.js` → `overseer.js`, `index.production.html` → `index.html`, and `overseer.css` to nginx (local or SSH).
- **`_persist_file_trigger()`**: New helper that writes file-channel trigger outcomes into `orchestrator_triggers_local` with `ON DUPLICATE KEY UPDATE`.

### Changed
- `overseer.production.js` synced with `overseer.live.js` (all v2.2.1 fixes).
- Cache-buster bumped to `v2.2.2-triggertype`.
- `run_step()` signature now accepts `trigger_source` parameter.
- Subprocess `Popen` call includes `env` with `OVERSEER_ORCHESTRATOR_MANAGED=1`.

### AI Context Delta
- File-trigger pipeline: `Browser → PHP → SFTP pull → pending/ → consume_file_cycle → execute_pipeline + _persist_file_trigger → orchestrator_triggers_local`. Previously the last step was missing.
- `OVERSEER_ORCHESTRATOR_MANAGED` env var: when `"1"`, the pipeline's own monitor skips `finish()` DB write. Only the orchestrator's monitor writes to `pipeline_runs`.
- `_persist_file_trigger()` uses `ON DUPLICATE KEY UPDATE` on `trigger_id` (UNIQUE in `orchestrator_triggers_local`).
- Frontend dedup order: `[...dbRuns, ...dbTriggerRows, ...localStorage]` — DB "consumed" supersedes localStorage "queued" via same `trigger_id` key.
- `deploy-frontend` reuses `_load_ssh_config()` / `_resolve_ssh_key()` for SSH deployment.
## [2.2.2] - 2026-02-25

### Fixed
- **Duplicate DB records**: When orchestrator launches a pipeline via `subprocess.Popen`, the child process now receives `OVERSEER_ORCHESTRATOR_MANAGED=1` env var. The pipeline's own `OverseerMonitor.finish()` is skipped when this var is set, eliminating the double INSERT into `pipeline_runs` (orchestrator monitor + pipeline monitor).
- **Run Now stuck at "queued"**: Production JS (`overseer.production.js`) was out-of-sync with `overseer.live.js` — missing the v2.2.1 dedup, `lineageSelectedPipelineId`, and localStorage pruning fixes. Synced and cache-buster bumped.
- **`trigger_type` hardcoded to "manual"**: `run_step()` in `orchestrator.py` was ignoring the actual `trigger_source` parameter. Now propagated correctly from `execute_pipeline()` → `run_step()` → `step_ctx`.

### Added
- **`triggerType` column in `pipeline_runs`**: Auto-created via `ensure_tables()` migration (`VARCHAR(64) NULL`). Values: `manual`, `trigger_file`, `trigger_db`, `schedule`, etc. Exposed in export payload and frontend JSON.
- **`deploy-frontend` command**: `python orchestrator.py deploy-frontend` copies `overseer.production.js` → `overseer.js`, `index.production.html` → `index.html`, and `overseer.css` to the nginx directory (local path or SSH).

### Changed
- `run_step()` signature now accepts `trigger_source: str = "manual"` parameter.
- `RunRecord` dataclass includes `trigger_type` field; `to_run_summary()` emits `triggerType`.
- Export `fields` list includes `triggerType`.
- Cache-buster updated to `v2.2.2-triggertype`.

### AI Context Delta
- `OVERSEER_ORCHESTRATOR_MANAGED=1` env var — when set, pipelines must skip their own DB write to `pipeline_runs`. Currently only `microsoft_forms_2_datalake/src/main.py` checks it; new pipelines should follow same pattern.
- `triggerType` column is optional; `overseer_monitor/db/writer.py` already introspects table columns and writes `triggerType` if the column exists.
- `deploy-frontend` reuses `_load_ssh_config()` and `_resolve_ssh_key()` from the SFTP trigger pull code.
- Production JS and live JS are now identical at v2.2.2.

## [2.2.1] - 2026-02-24

### Fixed
- **Runs disappearing on refresh**: `renderLineage()` was silently mutating `state.selectedPipelineId` to the first pipeline in the lineage view. On next 30s refresh, `applyRunFilters()` would then filter runs to only that pipeline, making it appear as though runs vanished. Introduced separate `lineageSelectedPipelineId` state — lineage tile selection no longer pollutes the global run filter.
- **Search not working**: Typing in the search box now clears `selectedPipelineId` so results aren't filtered to a single pipeline, and switches to the Runs view automatically when there's a query.
- **Run now stuck at "queued"**: Scheduler step reordering — `consume_remote_triggers()` (SFTP pull) now runs BEFORE `consume_file_triggers()`, eliminating the one-tick delay where remote triggers landed in `pending/` but weren't consumed until the next cycle.
- **Orchestration history noise**: `orchRuns` are now deduplicated by `runId` (DB runs + trigger rows + localStorage were triple-sourced). localStorage trigger history pruned to max 50 items / 7 days.

### Changed
- **Update info moved to header**: "Última atualização" timestamp and run count now display in the header bar next to the refresh countdown, instead of in a banner below the nav tabs.
- **Quick filter removed from header**: The `<select id="quickFilter">` dropdown has been removed from the header. Time/status filters remain in the Runs view controls.
- `updateFooter()` now also writes to `headerUpdateTime` and `headerUpdateRuns` elements.
- Cache-buster bumped to `no-api-v3-3`.

### AI Context Delta
- `state.lineageSelectedPipelineId` is the new property for lineage tile selection. `state.selectedPipelineId` is only set by pipeline table click or explicit user action — never by renderLineage().
- Scheduler steps reordered: 6=remote pull, 7=file triggers, 8=schedule triggers (was 6=file, 7=schedule, 8=remote).
- `#quickFilter` HTML element removed. Its JS handler still exists but is inert (no element to bind to).

## [2.2.0] - 2026-02-24

### Added
- **Server-side trigger delivery**: "Run now" and "Schedule change" buttons in the frontend now POST trigger JSON directly to a PHP endpoint on the nginx server (`/MAIATRON/apps/overseer/trigger.php`). No downloads, no file picker, no CLI copy — one click to submit.
- **PHP trigger receiver** (`runtime/trigger.php`): minimal PHP script that accepts POST JSON and writes trigger files to `triggers/` directory on the nginx server. Supports GET health check.
- **Remote trigger pull via SFTP** (`consume_remote_triggers()` in `orchestrator.py`): scheduler daemon step 8 — uses paramiko/SFTP to fetch trigger files from nginx server, routes "run now" triggers to `runtime/run_now_channel/pending/` and "schedule change" triggers to `runtime/triggers/schedule/pending/`, then deletes remote originals.
- **`_load_ssh_config()` and `_resolve_ssh_key()` helpers** in orchestrator.py for reusable SSH config loading.

### Fixed
- **"Indisponível neste browser"**: `writeRunNowTrigger` and `writeScheduleTrigger` no longer use `window.showDirectoryPicker` (requires HTTPS, site uses HTTP) or blob downloads (user-rejected). Replaced with `fetch()` POST to PHP endpoint.
- **Lineage helpers restored** (from v2.1.0 hotfix): 7 helper functions (`lineageEventLevel`, `lineagePipelineSummary`, `lineageStateClass`, `lineageStateLabel`, `ensureLineageLogModal`, `closeLineageLogModal`, `openLineageLogModal`) that were accidentally deleted during dead code cleanup.

### Changed
- Toast messages simplified: "Run now enviado com sucesso" / "Schedule de X alterado com sucesso" — no mention of files or directories.
- Removed unused `runNowDirHandle` variable from JS.
- Scheduler daemon docstring updated to list all 8 steps.

### Architecture
```
Browser → POST /MAIATRON/apps/overseer/trigger.php (port 80, HTTP)
       → PHP writes JSON file to triggers/ directory on nginx server
       → Scheduler daemon (HP-Z2-EF) pulls via SFTP each tick (~60s)
       → Routes to run_now_channel/pending/ or triggers/schedule/pending/
       → Existing consume_file_triggers() / consume_schedule_triggers() process them
```

### AI Context Delta
- Trigger delivery is now fully server-side. Frontend uses `/MAIATRON/apps/overseer/trigger.php` (configurable via `window.OVERSEER_ASSETS.triggerUrl`).
- The PHP endpoint is at `/usr/share/nginx/html/MAIATRON/apps/overseer/trigger.php`. The triggers/ directory must be writable by `www-data` (chmod 777).
- `consume_remote_triggers()` uses SSH config from `secrets/database.json → ssh` block (same as export script).
- The `overseer_trigger_receiver.py` (Python HTTP server) was deployed but replaced by PHP — it's kept in `runtime/` as reference but not running.
- Production JS now ~318 lines, 57,004 bytes.

## [2.1.0] - 2026-02-18

### Added
- **Schedule editing from frontend**: orchestrator tab now shows editable schedule field per pipeline. Owners can modify cron expressions directly; saved via trigger file mechanism (`runtime/triggers/schedule/`).
- **CLI `schedule set|show`**: `python orchestrator.py schedule set <pipeline_id> "<cron|manual>"` rewrites YAML atomically. `schedule show` lists all pipeline schedules.
- **Schedule trigger consumption**: scheduler daemon (step 7) scans `runtime/triggers/schedule/pending/` each tick, validates cron, rewrites YAML, archives to `done/` or `failed/`.
- **Permission enforcement in frontend**: orchestrator "Run now" button disabled for users without `owner`/`executor` role. Role badges (owner/executor/viewer/open) shown per pipeline.
- **Update banner**: prominent last-update info relocated to banner below nav tabs (removed from footer).
- **Comprehensive lineage CSS**: ~200 new CSS rules for v5 layout — `.lineage-shell` 2-column grid, `.lineage-tiles` sidebar, `.lineage-pipeline-tile` cards, `.lineage-hero` detail, `.lineage-filter-row`, `.lineage-dep-chip`, `.lineage-log-actions`, and more.
- **CSS versioned locally**: `runtime/overseer.css` now tracked in repo (downloaded from nginx).
- **New CSS for**: `.schedule-cell`, `.schedule-input`, `.btn-schedule-save`, `.role-badge` (owner/executor/viewer/open variants), `.update-banner`, `.update-banner-dot`.

### Fixed
- **Runs disappearing on 30s refresh**: wired `#timeFilter` select (was completely dead — zero JS listeners). Added date filtering logic to `applyRunFilters()` with 24h/7d/30d/all options.
- **Runs disappearing on filter**: wired `#q` search input with live `applyRunFilters()` + `renderRuns()` calls.
- **quickFilter sync**: `nok_24h`/`nok_7d` quick filters now sync the time period dropdown correctly.
- **"Arrow" above periodo de runs**: removed orphan `.controls` div containing dead `#qField` select, `#doSearch`, `#clearFilters` buttons.
- **Lineage layout broken**: added all missing v5 CSS classes (was only 5 basic rules; now ~50 comprehensive rules).

### Changed
- Footer simplified to "OVERSEER © 2026" (removed dynamic year, run count, table label).
- Monitoring descriptions rewritten in Portuguese with detailed explanations for each indicator (signal hints, calc-info, metric tooltips).
- Orchestrator description updated to mention schedule editing and user permissions.

### Removed
- **Dead renderLineage v1-v4**: removed ~262 lines of stacked dead code (4 obsolete renderLineage definitions + associated helper functions). Only v5 remains.
- Orphan HTML controls div (qField, doSearch, clearFilters).

### AI Context Delta
- Frontend schedule editing uses file trigger pattern: JS writes `schedule-{pipeline_id}-{ts}.json` → scheduler daemon consumes from `runtime/triggers/schedule/pending/` → rewrites YAML.
- `runtime/overseer.css` is now versioned locally (was only on nginx). All changes go through this file.
- Permission enforcement: frontend checks `pipeline_permissions` from payload. `getUserRole()`, `canUserRunPipeline()` helpers in JS.
- Production JS is now 242 lines (was ~516 before dead code cleanup).

## [2.0.0] - 2026-02-17

### Added
- **Scheduler daemon** (`python orchestrator.py scheduler`): absorve export, archive, digest, trigger consume e pipeline schedules. Zero dependência de cron. Cross-platform (Windows + Linux).
- **LineageEmitter** (`overseer_monitor/lineage_emitter.py`): helper zero-DB para pipelines emitirem marcadores `@@OVERSEER_MODULE@@` em stdout. O orchestrator intercepta e persiste em `pipeline_module_events`.
- **WARNING como terceiro estado**: módulos com `critical: false` que falham geram WARNING (amarelo) em vez de NOK. Lógica: todos critical OK + algum non-critical NOK = WARNING.
- **Permissões por pipeline**: tabela `overseer_pipeline_permissions` ligada a `MAIATRON.auth_users`. CLI: `user list|grant|revoke|show`.
- **`entrypoint_windows`** no YAML: comando alternativo para Windows. Selecionado automaticamente via `platform.system()`.
- **`critical` flag nos steps** do YAML: `critical: true|false` (default true).
- **Slack WARNING**: notificações com emoji `:warning:` e lista de módulos não-críticos falhados.
- **Export payload**: inclui `pipeline_permissions` e `critical` flag nos nós de `module_lineage`.
- **Frontend lineage**: módulos mostram badge "non-critical" quando aplicável.

### Changed
- `orchestrator.py` `run_step()`: usa `subprocess.Popen` com streaming linha-a-linha em vez de `subprocess.run`. Parseia marcadores de lineage em tempo real.
- `orchestrator.py` `execute_pipeline()`: determina status final como `success`/`warning`/`failed` com base em módulos críticos vs não-críticos.
- `overseer_monitor/monitor.py` `finish()`: aceita status WARNING. Normalização: `warning/warn/parcial` → WARNING.
- Frontend: status-pills suportam 3 estados (OK verde, WARNING amarelo, NOK vermelho) em pipelines e runs.
- Template `pipelines/_template/pipeline.yaml`: inclui `entrypoint_windows` e exemplo de steps com `critical`.

### Removed
- **Kiosk mode**: removidos todos os elementos kiosk do frontend (`kioskFailed`, `kioskAtRisk`, `kioskStale`, `kioskRegressions`, `kioskVolume`, `kioskHeadline`, `kioskSubline`, `kioskPriorityList`, `kioskIncidentsList`, `kioskRunsHistoryChart`, `kioskSuccessRateChart`).
- Variáveis globais `kioskHistoryChart` e `kioskHealthChart`.

### AI Context Delta
- O scheduler daemon substitui todos os cron jobs. Usar `python orchestrator.py scheduler` como serviço.
- Lineage passa por stdout markers (`@@OVERSEER_MODULE@@`), não por escrita direta na DB pelo pipeline.
- WARNING é o terceiro estado: critical modules OK + non-critical NOK = WARNING.
- Permissões de pipeline lidas de `MAIATRON.auth_users` + `overseer_pipeline_permissions`.
- Frontend sem kiosk. Status-pills com 3 cores.
- `microsoft_forms_2_datalake` instrumentado com `LineageEmitter` (9 módulos).

---
## [1.6.7] - 2026-02-16

### Changed
- Frontend `Runs`: removidos controlos locais `Pesquisar` e `Limpar`; ordenacao passa a ser por clique no cabecalho da coluna (toggle asc/desc).
- Frontend `Runs`: comparadores numericos/datetime/texto alinhados para `#`, `Inicio/Fim`, `Duracao`, `CPU`, `Memoria`, `Pipeline`, `Estado`, `Host`, `SO`.
- Frontend `Lineage`: passa a mostrar inventario de scripts por pipeline (`src`) e scripts observados em runtime.
- Frontend `Orquestracao`: estados normalizados (`queued|running|consumed|failed`) e origem explicita quando a acao ficou em fallback `CLI copy`.

### Added
- Export payload inclui novo bloco `pipeline_scripts` no contrato no-API.

### Fixed
- `scripts/export_payload_from_db.py`: removidas duplicacoes de `_cleanup_local_legacy_files` e `_cleanup_ssh_legacy_files`.
- Publicacao frontend mantida apenas para `overseer_payload.json` e `overseer_details.json`, com limpeza de legados `pm_payload.json`/`pm_details.json`.

### AI Context Delta
- A vista `Runs` deixou de filtrar por clique em celula; agora ordena por cabecalho.
- `pipeline_scripts` e a fonte de verdade para lineage tecnico no frontend.

---
## [1.6.6] - 2026-02-16

### Changed
- `RUNS_TABLE` alinhado para `pipeline_runs` no ambiente local.
- Frontend `Runs`: removida coluna `Script`, modal simplificado (Pipeline + SO), filtro por clique reforcado via delegacao no `tbody`.
- `pipeline_module_events.contextJson.script_command` passa a alimentar labels de lineage com o script/comando real do pipeline.

### Fixed
- Compatibilidade de escrita na tabela `pipeline_runs`:
  - status `OK/NOK` mapeado para `Success/Failed` quando aplicavel;
  - criticality normalizada para enum (`Low|Medium|High|Critical`);
  - `execTime` convertido para `TIME` quando necessario.

### AI Context Delta
- Lineage mostra scripts reais (ex.: `src/main.py`) por pipeline.
- Runs em `pipeline_runs` voltam a ser persistidas sem erro de truncation.

---

## [1.6.5] - 2026-02-16

### Changed
- Vista `Runs` no frontend: coluna `Run Pipeline` mostra apenas `pipelineId` (sem sufixo `#run_id`).
- Tabela `Runs` permite filtro por clique direto nas colunas (status, pipeline, script, host e SO).
- Cards de resumo (`Execucoes`, `Sucesso`, `Tempo medio`, `Recursos`) removidos da area de Runs.
- `runs` passa a registar `osName`, `osRelease`, `osPlatform` para segmentacao de recursos por sistema operativo.

### AI Context Delta
- Segmentacao de recursos por SO ja disponivel para runs novas.
- UX de filtragem em Runs esta centrada em interacao por coluna.

---

## [1.6.4] - 2026-02-16

### Changed
- `run_step` passa a registar sempre eventos em `pipeline_module_events` sem criar entradas duplicadas na tabela `runs`.
- Logs de `stdout/stderr` passam por limpeza de ANSI antes de persistir em `logMessage`.
- Modal de detalhe no frontend live usa classes corretas (`metric-card`) e renderiza logs sem códigos ANSI.

### AI Context Delta
- Cada execução mantém uma única run principal em `runs`, mas com detalhe completo por módulo em `pipeline_module_events`.
- O modal do Overseer deixa de aparecer desformatado quando abre detalhes de run.

---

## [1.6.3] - 2026-02-13

### Changed
- `orchestrator.py run <pipeline_id>` passa a disparar automaticamente `scripts/export_payload_from_db.py` no fim da execução.
- `orchestrator.py` agrega `stdout/stderr` de steps e persiste em `logs.logMessage` para leitura no modal do frontend.

### Fixed
- Alinhado `RunRecord` com o campo `log_message` no runtime de export.
- Eventos de módulo passam a aceitar `logMessage` quando presente no contexto.

### AI Context Delta
- Runs de sucesso também podem expor detalhes técnicos em `logMessage` (não apenas erros).
- Atualização de frontend por run deixa de depender de export manual.

---
## [1.6.2] - 2026-02-13

### Added
- `scripts/export_payload_from_db.py` passa a publicar automaticamente os JSON do frontend no nginx em `/usr/share/nginx/html/MAIATRON/apps/overseer`.
- Estratégia de publicação: copy local quando o path existe (runner Ubuntu), ou upload via SSH (SFTP) quando corre noutra máquina.

### AI Context Delta
- Export fica independente do runner para entrega no nginx final.

---
## [1.6.1] - 2026-02-13

### Changed
- Runtime DB (`src/pm_runtime/db.py`) passa a suportar tunel SSH automatico via bloco `ssh` em `secrets/database.json`.
- `orchestrator.py` passa a usar DB URL efetivo (`get_db_url()`), garantindo consistencia com ligacao tunelada.

### Fixed
- Eliminada necessidade de abrir `ssh -L` manual para `orchestrator.py` e `scripts/export_payload_from_db.py` quando existe `ssh_key` configurada.

### AI Context Delta
- Para ambiente com MySQL acessivel apenas via SSH, basta preencher `secrets/database.json` (global) com blocos `ssh` + `database`.

---
Este projeto segue **Semantic Versioning** (`MAJOR.MINOR.PATCH`).
Formato inspirado em Keep a Changelog, com secao extra para IA: `AI Context Delta`.
## [1.6.0] - 2026-02-13

### Added
- Pipeline microsoft_forms_2_datalake integrado em pipelines/microsoft_forms_2_datalake para execução direta via orchestrator em Windows.
- Estrutura copiada para padrão Overseer (src/, config/, secrets/ com exemplos apenas).

### Changed
- Nomenclatura do monitor do pipeline migrada para Overseer (overseer_monitor, OverseerMonitor).
- Dependências do projeto atualizadas para suportar execução do pipeline de Forms/Excel (pandas/openpyxl/sshtunnel/paramiko, etc.).

### AI Context Delta
- Pipeline pronto para python orchestrator.py run microsoft_forms_2_datalake após preencher pipelines/microsoft_forms_2_datalake/secrets/.
- Nenhum segredo real foi copiado para o repositório.

---

## [1.5.0] - 2026-02-10

### Changed
- Rebranding documental e operacional consolidado para `Overseer`.
- Exemplos de deploy e cron atualizados para path Linux `/opt/overseer`.
- URLs exemplo de frontend alinhadas com `/apps/overseer/PM.html`.
- Ficheiro de import preferencial adicionado: `overseer.py`.

### AI Context Delta
- Nome canónico do projeto passou a ser **Overseer**.
- Runtime principal mantém contrato no-API: `DB -> JSON -> frontend`.
- Artefactos de frontend mantêm os mesmos nomes para compatibilidade:
  - `frontend/pm_payload.json`
  - `frontend/pm_details.json`

---

## [1.4.0] - 2026-02-09

### Added
- Modo `Run now` sem API no frontend (ação direta de trigger no canal operacional).
- Novo comando no orchestrator:
  - `python orchestrator.py trigger consume-file --dir <canal> --runner <hostname> --once --max <n>`
- Canal de execução por ficheiros com pastas:
  - `pending`, `processing`, `done`, `failed`
- Cron recomendado para consumo do canal de `Run now`.

### Changed
- UI de Orquestração atualizada:
  - botão `Run now` (sem referência visual a shared file)
  - fallback para comando CLI quando o browser não suporta escrita local segura
- Notificação Slack por run mantém foco em `NOK`.
- Documentação atualizada (`README` + PRD + guia de produção).

### AI Context Delta
- Para experiência “run now” sem API:
  1. ativar `trigger consume-file` no runner;
  2. manter export de 15 min para refletir no frontend;
  3. manter consumo DB-trigger para cenários de compatibilidade.

---

## [1.3.0] - 2026-02-09

### Added
- PRD mestre universal: `docs/PRD_PM_Universal_DropIn_AI_Ready.md`.
- Checklist operacional para agentes: `docs/AI_HANDOFF_CHECKLIST.md`.
- Guia de agentes no repositorio: `AGENTS.md`.
- `.gitignore` completo para secrets, runtime e artefactos gerados.
- `frontend/` como pasta canónica da UI (`PM.html`, `pm.css`, `pm.js`, payloads).
- Script de resumo diario Slack: `scripts/slack_daily_digest.py`.

### Changed
- Runtime no-API consolidado (`DB -> JSON -> frontend`).
- Export passa a escrever em:
  - `frontend/pm_payload.json`
  - `frontend/pm_details.json`
- `runner_host` com comportamento deterministico:
  - `auto`/vazio => hostname local
  - `any` => qualquer runner
  - hostname explicito => runner fixo
- Trigger queue multi-maquina em DB:
  - `orchestrator_triggers_local`
  - consumo por `python orchestrator.py trigger consume --runner <hostname>`
- URLs de frontend atualizadas para `.../frontend/PM.html`.
- `overseer_monitor` notifica Slack apenas em `NOK` por default (`notify_on_ok=false`).

### Removed
- Dependencia operacional de backend/API no caminho critico.
- Fluxo legado de trigger por ficheiro (`runtime/triggers/pipeline_triggers.jsonl`) como mecanismo principal.
- Ficheiros de frontend redundantes na raiz do workspace.

### AI Context Delta
- Objetivo atual do sistema: operar sem APIs HTTP no runtime principal.
- Ficheiros fonte de verdade para onboarding:
  - `README.md`
  - `docs/PRD_PM_Universal_DropIn_AI_Ready.md`
  - `docs/AI_HANDOFF_CHECKLIST.md`
  - `pipelines/_template/`
- Comandos minimos de validacao apos alteracoes:
  - `python orchestrator.py list`
  - `python scripts/export_payload_from_db.py`
- Saida esperada para UI:
  - `frontend/pm_payload.json`
  - `frontend/pm_details.json`

---

## [1.2.0] - 2026-02-09

### Added
- Orquestracao multi-maquina por DB queue com `runner_host`.
- Export inclui metadados de orquestracao (`orchestrator_runs`, `orchestrator_triggers`).
- Instrumentacao por modulo para lineage (`pipeline_module_events`).

### Changed
- `orchestrator.py` passou a descobrir pipelines em `pipelines/**`.
- `cwd` de execucao alinhado com a pasta do pipeline.

### AI Context Delta
- Mudancas focadas em scheduling/triggering e lineage.
- Nenhuma alteracao de contrato principal do `overseer_monitor.start()/finish()/step()`.

---

## [1.1.0] - 2026-02-09

### Added
- Estrutura homogénea por pipeline:
  - `pipelines/<pipeline_id>/pipeline.yaml`
  - `pipelines/<pipeline_id>/src`
  - `pipelines/<pipeline_id>/config`
  - `pipelines/<pipeline_id>/secrets`
- Template oficial em `pipelines/_template`.

### Changed
- Runtime comum movido para `src/pm_runtime`.
- Documentacao inicial de operacao no-API.

### AI Context Delta
- Base estrutural para projetos drop-in.
- A partir desta versao, novas pipelines devem sempre nascer de `_template`.

---

## [1.0.0] - 2026-02-09

### Added
- Primeira baseline operacional no-API:
  - `orchestrator.py`
  - `scripts/export_payload_from_db.py`
  - `scripts/archive_logs.py`
  - frontend estático.

### AI Context Delta
- Versao de referencia inicial para modo `DB -> JSON -> frontend`.




