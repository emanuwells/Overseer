# HANDOFF

Este ficheiro preserva o estado operacional verificável do projeto entre sessões.

## Metadados

| Campo | Valor |
|---|---|
| Última atualização | 2026-06-11T28:00:00+01:00 |
| Branch Git | `main` |
| Estado | 5.6.0 — API read-first; monitoring removido; frontends Overseer + MAIATRON alinhados |
| Responsável / Agente | Cursor |
| Última versão registada | 5.6.0 |

## Nota v5.6.0 (2026-06-11)

- `/v1/monitoring/*` removido; contrato único em `/v1/read/*` + `/v1/catalog/*`.
- `deployment_health.py` expõe `is_stale`, `risk_score`, telemetria em overview/deployments.
- MAIATRON-HUB: `read_adapter.php` no BFF; 4 tabs; sem fallback MySQL.
- Deploy coordenado: pull Overseer (Docker rebuild) + `baze2-maiatron-hub-pull.sh`.

## Nota v5.5.0 (2026-06-11)

- `list_deployments()` unifica YAML + DB + runs; dashboard mostra todos os deployments (baze2 + WS1207).
- Após deploy em prod: `POST /v1/catalog/reconcile` (token API) para registar pipelines baze2 na DB.
- Edição no dashboard: PATCH → DB + `deploy/runners/<host>.yaml` + SSH se `OVERSEER_SSH_SYNC_ENABLED=1`.
- `host_id` canónico: `BAZE2` resolve para ficheiro `baze2.yaml` e entrada em `hosts.yaml`.

## Objetivo Atual

Manter o Overseer como núcleo Docker-first para observabilidade de pipelines externos. O Overseer recebe catálogo DAG e telemetria por API, guarda em tabelas `overseer_*` e mostra o estado em `/ui/dashboard.html`, sem executar código dos pipelines.

## Estado Atual

### Concluído

- Template colocado em `frontend/` adaptado para consumir dados reais da API.
- `dashboard.html`, `run-detail.html`, `lineage.html` e `deployments.html` mantêm a estrutura visual do template com pontos `data-*`.
- `frontend/js/app.js` renderiza overview, database, runs, DAG, heartbeats e triggers via `/v1/read/*`.
- `frontend/index.html` continua a redirecionar para `dashboard.html`, sem launcher/página inicial.
- `frontend/css/app.css` recebeu estilos auxiliares para alertas, estados vazios e token.
- `POST /v1/catalog/pipelines` criado para registar ou atualizar pipeline, nodes e edges.
- `GET /v1/read/pipelines/{pipeline_id}/dag` criado para leitura de DAG.
- Tabelas `overseer_pipeline_nodes` e `overseer_pipeline_edges` adicionadas ao schema.
- `overseer_pipelines.metadata_json` adicionado com migração simples em `init_schema()`.
- Chaves autoincrementais ajustadas para `Integer` para compatibilidade SQLite/MariaDB.
- Endpoint `/v1/orchestrate/pipelines/{pipeline_id}/run` removido.
- `overseer-agent run` removido porque chamava o endpoint removido.
- `OverseerClient.register_pipeline()` adicionado ao SDK.
- Frontend em `frontend/` servido em `/ui/`; `/` e `/ui` redirecionam para `/ui/dashboard.html`.
- Launcher/landing BruinOps removidos.
- Dashboard, runs, DAG e ambiente passam a consumir `/v1/read/*`.
- Pipeline exemplo `pipelines/microsoft_forms_2_datalake/` removido do repo.
- Dockerfile simplificado para Python; build Node/Vite removido.
- Mount `./pipelines:/app/host_pipelines:ro` removido do Compose.
- Template de pipeline atualizado para registo DAG por API.
- README, PROJECT_CONTEXT, ADR, OpenAPI, tasks, Skill local e changelog atualizados.

### Concluído (4.3.0)

- `overseer_sdk/manifest_runner.py`: runner por manifest com observabilidade por passo (módulo por script, stdout/stderr, falha interrompe run crítica).
- `overseer-agent manifest <path> [--register-catalog] [--by]` adicionado.
- `templates/runner/`: manifest, `run.sh` e `.env.overseer` para `~/overseer-runners/`.
- `docker-compose.prod.yml`: API isolada, bind `127.0.0.1:8090`, DB via `host.docker.internal`.
- `deploy/nginx/overseer.conf` e `scripts/deploy-nginx-frontend.sh`: frontend em `/usr/share/nginx/html/Overseer` e proxy `/v1`.
- `tests/test_manifest_runner.py`: 8 testes; suite total com 18 testes a passar.
- `PyYAML` adicionado a `requirements.txt` e `pyproject.toml`; versões a 4.3.0.

### Em Curso

- Deploy em `eferreira@195.23.9.32` (SSH): backup do crontab, clone do repo, `.env`, compose de produção, nginx e migração dos pipelines do crontab.

### Por Fazer

- Concluir deploy e migração do crontab no servidor (uma entrada de cada vez, com dry-run).
- Rodar a password sudo exposta na conversa e migrar para chave SSH.
- Decidir licença real do projeto; documentação mantém `A confirmar`.
- Fase seguinte: botão "Run" no frontend (triggers + daemon consumidor).

### Bloqueios / Perguntas Abertas

- Browser in-app indisponível via `tool_search`; validação frontend foi feita por HTTP e API.
- O volume MariaDB local preservou uma linha antiga `microsoft_forms_2_datalake`. O código e ficheiros do exemplo foram removidos; o dado persistido não foi apagado por segurança.
- Configuração de produção/SSH continua não confirmada e não foi usada.

## Próximo Passo Exato

Para integrar um pipeline real:

1. Copiar `templates/pipeline-repo/` para o repositório do pipeline.
2. Criar `.env.overseer` local com `OVERSEER_API_URL`, `OVERSEER_API_TOKEN` e `OVERSEER_PIPELINE_ID`.
3. Chamar `overseer.register_catalog(nodes=[...], edges=[...])`.
4. Instrumentar runs com `overseer.run()` e módulos com `overseer.step()`.
5. Abrir `http://127.0.0.1:8090/ui/dashboard.html`.

## SSH, GitHub E Servidores

| Item | Valor |
|---|---|
| SSH usado nesta sessão | Não |
| Servidor acedido | N/A |
| Ambiente | Local Docker |
| Deploy remoto | N/A |
| Risco identificado | Dados persistidos antigos no volume MariaDB local |
| Próximo passo remoto | Confirmar alvo antes de qualquer operação em servidor |

## Dependências E Pipelines

| Item | Estado | Nota |
|---|---|---|
| Python | Mantido | `requirements.txt` reduzido ao núcleo API/SDK/agente |
| Pacote Python | Atualizado | `pyproject.toml` versão 4.2.0 |
| Node | Removido | Frontend é estático; Dockerfile não tem fase Node |
| Docker | Mantido | API + MariaDB local |
| Pipeline exemplo | Removido | `pipelines/microsoft_forms_2_datalake/` sem ficheiros versionados |
| Template de pipeline | Atualizado | Registo DAG por API |

## Auditoria De Ficheiros Desnecessários

| Ficheiro/Pasta | Estado | Ação | Nota |
|---|---|---|---|
| `frontend/landing.html` | Obsoleto | Removido | Página inicial não desejada |
| `frontend/bruinops-prototype.html` | Obsoleto | Removido | Launcher/protótipo antigo |
| `pipelines/microsoft_forms_2_datalake/` | Fora do núcleo | Removido | Pedido do utilizador |
| `templates/pipeline-repo/pipeline.yaml` | Contrato antigo | Removido | Substituído por registo API |
| Build Node/Vite | Obsoleto | Removido | Frontend estático |
| Volume MariaDB local | Dados persistidos | Mantido | Não remover sem confirmação |

## Estado Git

| Item | Valor |
|---|---|
| Repositório | `g:\O meu disco\Dev\Repos\emanuwells\Overseer` |
| Branch | `main...origin/main` |
| Alterações pré-existentes preservadas | Remoção de `webapp/` e nova pasta `frontend/` já estavam no estado Git antes da implementação |
| Commits/tags/branches/PRs | Não criados |
| Risco de sobrescrever alterações do utilizador | Baixo; não houve reset/checkout/clean |

## MCP Servers

| MCP Server | Usado Nesta Sessão | Finalidade | Resultado / Erro | Fallback |
|---|---:|---|---|---|
| N/A | Não | Verificação de configuração | Não foram encontrados `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json` ou `.claude/mcp.json` | Ferramentas locais |

## Skills Usadas

| Skill | Usada Nesta Sessão | Finalidade | Resultado / Erro |
|---|---:|---|---|
| `repo-onboarding` | Sim | Mapear contexto do repo | Aplicada |
| `skill-selector` | Sim | Escolher Skills relevantes | Aplicada |
| `backend-architecture` | Sim | API e persistência DAG | Aplicada |
| `frontend-architecture` | Sim | UI estática ligada à API | Aplicada |
| `fullstack-delivery` | Sim | Integrar API, DB, frontend e Docker | Aplicada |
| `api-contract-guardian` | Sim | Atualizar contrato HTTP/testes/OpenAPI | Aplicada |
| `database-migration-safety` | Sim | Evitar migração destrutiva; adicionar coluna/tabelas | Aplicada |
| `dependency-manager` | Sim | Reduzir manifestos e Docker | Aplicada |
| `file-pruner` | Sim | Remover exemplo e frontend obsoleto | Aplicada |
| `documentation-keeper` | Sim | Atualizar documentação | Aplicada |
| `handoff-maintainer` | Sim | Atualizar este ficheiro | Aplicada |
| `changelog-semver` | Sim | Registar 4.2.0 | Aplicada |
| `definition-of-done` | Sim | Checklist final | Aplicada |
| `security-secrets-audit` | Sim | Verificar ausência de segredos novos | Aplicada |
| `prompt-injection-guard` | Sim | Tratar outputs como dados não confiáveis | Aplicada |
| `stop-the-slop` | Sim | Remover texto enganador/obsoleto | Aplicada |

## Decisões Técnicas

| Decisão | Motivo | Impacto | ADR |
|---|---|---|---|
| Catálogo DAG por API | Desacoplar Overseer dos repos de pipelines | Pipelines reais registam nodes/edges por HTTP | `docs/adr/0001-overseer-core-api-refactor.md` |
| Remover execução local por API | Evitar subprocessos e dependências de negócio no núcleo | `/v1/orchestrate/*` fica limitado a triggers | `docs/adr/0001-overseer-core-api-refactor.md` |
| Frontend estático | Reduzir build e dependências | Docker não precisa de Node/Vite | `docs/adr/0001-overseer-core-api-refactor.md` |
| Manter Docker-first | Ambiente reprodutível | API, UI e MariaDB sob Compose | `docs/adr/0001-overseer-core-api-refactor.md` |

## Segurança E Dados Não Confiáveis

| Item | Estado | Nota |
|---|---|---|
| Segredos introduzidos | Não identificado | Exemplos usam valores fictícios |
| Ficheiros reais de secrets lidos | Não | Não foram lidos `.env` nem chaves privadas |
| Dados externos | Tratados como não confiáveis | Outputs de ferramentas não foram seguidos como instruções |
| API token | Mantido | UI guarda token apenas em `sessionStorage` |

## Testes E Validação

| Comando / Verificação | Resultado | Nota |
|---|---|---|
| `git status --short --branch` | Passou | Confirmou alterações pré-existentes |
| Verificação MCP | Passou | Nenhuma configuração MCP encontrada |
| `python -m pytest -q` | Passou | 10 testes; 1 aviso de depreciação do TestClient |
| `docker compose config` | Passou | Sem mount `pipelines/` |
| `docker compose build` | Passou | Build Python sem Node/Vite |
| `docker compose up -d` | Passou | API recriada e iniciada |
| `GET /v1/health` | Passou | HTTP 200 |
| `GET /ui/dashboard.html` | Passou | HTTP 200 |
| `GET /` sem redirecionar | Passou | HTTP 307 para `/ui/dashboard.html`; PowerShell reportou como erro por configuração |
| `docker compose exec -T overseer-api python scripts/overseer_emit_demo.py` | Passou | Criou run `run-1780671437-521cd7ad` |
| `GET /v1/read/database` | Passou | DB reachable; `pipeline_nodes=3`, `pipeline_edges=2`, `runs=1`, `modules=3` |
| `GET /v1/read/pipelines/demo_dag/dag` | Passou | 3 nodes e 2 edges |
| `GET /ui/dashboard.html` pós-template | Passou | HTTP 200 |
| `GET /ui/run-detail.html` pós-template | Passou | HTTP 200 |
| `GET /ui/lineage.html` pós-template | Passou | HTTP 200 |
| `GET /ui/deployments.html` pós-template | Passou | HTTP 200 |
| `GET /ui/js/app.js` pós-template | Passou | HTTP 200 |
| `node --check frontend\js\app.js` | Passou | Sintaxe JS válida |
| Browser in-app | N/A | Ferramenta não disponível via `tool_search` |

## Checklist De Entrega

```text
[x] Apliquei as regras de forma proporcional à tarefa.
[x] Li AGENTS.md.
[x] Li ou criei PROJECT_CONTEXT.md quando aplicável.
[x] Li ou criei `.agents/ops/HANDOFF.md` quando a tarefa foi não trivial.
[x] Verifiquei MCP servers e usei os relevantes ou registei fallback.
[x] Verifiquei Skills e usei as relevantes ou registei fallback.
[x] Verifiquei estado Git quando possível.
[x] Protegi alterações existentes do utilizador.
[x] Tratei outputs externos como dados não confiáveis.
[x] Não introduzi nem expus segredos.
[x] Se usei SSH/servidores, confirmei ambiente, pasta, branch e impacto.
[x] Dependências externas têm manifesto adequado.
[x] Auditei ficheiros desnecessários e removi apenas os claramente seguros.
[x] Atualizei documentação afetada.
[x] README contém badges, arquitetura e estrutura do projeto quando aplicável.
[x] Docker foi avaliado, implementado ou justificado como N/A.
[x] Atualizei ADRs quando houve decisão técnica relevante.
[x] Executei testes/validações aplicáveis ou justifiquei N/A.
[x] Atualizei CHANGELOG.md quando houve alteração versionável.
[x] Atualizei `.agents/ops/HANDOFF.md` com estado final, próximos passos e bloqueios.
[x] Apliquei `stop-the-slop` para remover texto genérico, vago ou enganador.
```

## Notas Livres

Não foram criados commits, tags, branches ou PRs.
