# HANDOFF

Este ficheiro preserva o estado operacional verificável do projeto entre sessões.

## Metadados

| Campo | Valor |
|---|---|
| Última atualização | 2026-06-04T11:42:09+01:00 |
| Branch Git | `main` |
| Estado | Refactor 4.0.0 implementado; validação final executada nesta sessão |
| Responsável / Agente | Codex |
| Última versão registada | 4.0.0 |

## Objetivo Atual

Refatorar agressivamente o Overseer para um núcleo Docker-first com FastAPI, três superfícies HTTP canónicas, schema SQL simples, SDK/CLI para pipelines e frontend React/Vite local.

## Estado Atual

### Concluído

- API FastAPI reorganizada em:
  - leitura: `/v1/read/*`;
  - escrita/telemetria: `/v1/events/*`;
  - orquestração: `/v1/orchestrate/*`.
- Schema SQLAlchemy novo criado em `src/overseer_core/store.py` com tabelas `overseer_*`.
- MariaDB/MySQL mantido no Compose e portabilidade futura preparada via `OVERSEER_DB_URL`.
- SDK Python criado em `overseer_sdk/client.py`.
- CLI `python -m overseer_agent` atualizado para heartbeat, trigger, run e exec instrumentado.
- Adaptador `overseer_monitor.OverseerMonitor` mantido para pipelines que ainda usam a interface antiga, agora escrevendo via API.
- Frontend React/Vite criado em `webapp/` e servido em `/ui/`.
- Docker multi-stage validado com build Node + Python.
- Scripts de arranque multi-plataforma adicionados:
  - Windows CMD: `overseer-up.cmd`;
  - PowerShell: `scripts/overseer-up.ps1`;
  - Linux/macOS: `scripts/overseer-up.sh`;
  - fallback universal: `docker compose up --build -d`.
- Mantido apenas `pipelines/microsoft_forms_2_datalake` como exemplo.
- Removidos fluxos legados de export JSON, MAIATRON, scheduler CLI, pipeline template antigo e `webapp_medidata`.
- Valores com aparência de credencial e infraestrutura antiga removidos de exemplos/código de runtime.
- README, PROJECT_CONTEXT, OpenAPI, ADR, Skill local, changelog e plano atualizados.

### Em Curso

- N/A.

### Por Fazer

- Rever no futuro se `requirements.txt` pode ser ainda mais reduzido depois de estabilizar o pipeline Microsoft.
- Decidir licença real do projeto; a documentação mantém `A confirmar`.
- Se existir produção antiga dependente de JSON/MAIATRON, planear migração manual para a API v4.
- Rodar no sistema de origem qualquer credencial que possa corresponder aos valores antigos removidos de exemplos, caso tenha sido real ou reutilizada.

### Bloqueios / Perguntas Abertas

- `npm install` local em Windows/OneDrive falhou por permissões ao escrever `webapp/node_modules`; não bloqueia o fluxo suportado porque Docker instala tudo dentro da imagem.
- Pode existir uma pasta parcial `webapp/node_modules` local, ignorada por Git e excluída por `.dockerignore`.
- Configuração de produção/SSH continua não confirmada e não foi usada.

## Próximo Passo Exato

Executar o arranque Docker no sistema alvo:

```bash
docker compose up --build -d
```

Depois abrir:

- UI: `http://127.0.0.1:8090/ui/`
- API docs: `http://127.0.0.1:8090/docs`
- Health: `http://127.0.0.1:8090/v1/health`

## Proporcionalidade Aplicada

| Item | Valor |
|---|---|
| Tarefa trivial / não trivial | Não trivial |
| Fluxo completo aplicado | Sim |
| Justificação | Houve refactor de arquitetura, API, base de dados, frontend, Docker, documentação, ADR, Skill local, testes e remoção de ficheiros. |

## SSH, GitHub E Servidores

| Item | Valor |
|---|---|
| SSH usado nesta sessão | Não |
| Servidor acedido | N/A |
| Ambiente | Local |
| Deploy remoto | N/A |
| Risco identificado | Produção antiga pode depender do contrato removido |
| Próximo passo remoto | Confirmar alvo antes de qualquer operação em servidor |

## Dependências E Pipelines

| Item | Estado | Nota |
|---|---|---|
| Python | Mantido | `requirements.txt` continua a ser o manifesto da API e exemplo |
| Node | Adicionado | `webapp/package.json` e `webapp/package-lock.json` com versões fixas |
| Docker | Implementado | Build multi-stage instala Python e Node dentro da imagem |
| Pipeline exemplo | Mantido | `pipelines/microsoft_forms_2_datalake` |
| Outros pipelines | Removidos | `pipelines/webapp_medidata` e `_template` fora do novo contrato |

## Auditoria De Ficheiros Desnecessários

| Ficheiro/Pasta | Estado | Ação | Nota |
|---|---|---|---|
| `orchestrator.py` | Legado avariado após remoção de `pm_runtime` | Removido | Substituído pela API de orquestração |
| `src/pm_runtime/` | Legado | Removido | Contrato substituído por `src/overseer_core/store.py` |
| `src/overseer_api/routers/runners.py` | Router legado avariado | Removido | Heartbeat passa por `/v1/events/heartbeat` |
| `scripts/export_payload_from_db.py` | Legado JSON | Removido | Frontend passa a ler API |
| `pipelines/webapp_medidata/` | Fora de escopo | Removido | Pedido do utilizador |
| `pipelines/_template/` | Template obsoleto | Removido | Skill local atualizada para novo contrato |
| `migrations/` | Schema antigo | Removido | Novo schema é criado por SQLAlchemy |
| `docs/Guia_Producao_Step_by_Step.*` e PRDs antigos | Documentação contraditória | Removida | README/ADR passam a ser fonte atual |
| `webapp/node_modules/` | Artefacto local possível | Mantido se existir | Ignorado por Git e excluído por Docker |
| Host/IP antigo no runtime | Valor sensível ou ambiental | Removido | Usar `OVERSEER_DB_LOCAL_HOSTS` |

## Estado Git

| Item | Valor |
|---|---|
| Repositório | `g:\O meu disco\Dev\Repos\emanuwells\Overseer` |
| Branch | `main...origin/main` |
| Alteração pré-existente preservada | `PROJECT_CONTEXT.template.md` já aparecia como removido antes desta tarefa |
| Principais ficheiros alterados | `README.md`, `PROJECT_CONTEXT.md`, `CHANGELOG.md`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `openapi/overseer-api.yaml`, `tasks/todo.md`, `skills/overseer-pipeline/SKILL.md` |
| Principais ficheiros novos | `.dockerignore`, `src/overseer_core/store.py`, routers v4, `overseer_sdk/client.py`, frontend React/Vite, scripts `overseer-up`, ADR |
| Principais ficheiros removidos | `orchestrator.py`, `src/pm_runtime/`, routers legados, migrations antigas, export JSON, frontend legado, pipelines fora de escopo |
| Risco de sobrescrever alterações do utilizador | Baixo; não houve reset/checkout/clean e alterações existentes foram preservadas |

## MCP Servers

| MCP Server | Usado Nesta Sessão | Finalidade | Resultado / Erro | Fallback |
|---|---:|---|---|---|
| N/A | Não | Verificação de configuração | Não foram encontrados `.mcp.json`, `.cursor/mcp.json`, `.vscode/mcp.json` ou `.claude/mcp.json` | Ferramentas locais |

## Skills Usadas

| Skill | Usada Nesta Sessão | Finalidade | Resultado / Erro |
|---|---:|---|---|
| `repo-onboarding` | Sim | Mapear contexto do repo | Aplicada |
| `skill-selector` | Sim | Escolher Skills relevantes | Aplicada |
| `backend-architecture` | Sim | Desenhar API e store | Aplicada |
| `frontend-architecture` | Sim | Construir dashboard React/Vite | Aplicada |
| `fullstack-delivery` | Sim | Integrar API, DB, frontend e Docker | Aplicada |
| `api-contract-guardian` | Sim | Atualizar OpenAPI/testes | Aplicada |
| `database-migration-safety` | Sim | Evitar preservar schema antigo como contrato | Aplicada |
| `dependency-manager` | Sim | Manifestos Python/Node/Docker | Aplicada |
| `file-pruner` | Sim | Remover legado seguro | Aplicada |
| `security-secrets-audit` | Sim | Auditar exemplos e `.env` | Aplicada |
| `prompt-injection-guard` | Sim | Tratar outputs como dados não confiáveis | Aplicada |
| `documentation-keeper` | Sim | Atualizar README/contexto | Aplicada |
| `handoff-maintainer` | Sim | Atualizar este ficheiro | Aplicada |
| `changelog-semver` | Sim | Registar 4.0.0 | Aplicada |
| `definition-of-done` | Sim | Checklist final | Aplicada |
| `stop-the-slop` | Sim | Remover texto obsoleto/vago | Aplicada |

## README, Arquitetura E Docker

| Item | Estado | Nota |
|---|---|---|
| Badges no README | Atualizado | Stack, versão, Docker e licença a confirmar |
| Arquitetura no README | Atualizada | Mermaid com pipeline, API, DB e frontend local |
| Estrutura do projeto no README | Atualizada | Reflete o novo layout |
| Docker avaliado | Sim | Implementado como fluxo principal |
| Docker documentado | Sim | Comandos por SO e fallback `docker compose` |

## Ficheiros Relevantes

| Ficheiro | Estado | Nota |
|---|---|---|
| `src/overseer_core/store.py` | Novo | Schema e operações persistentes |
| `src/overseer_api/routers/*.py` | Novo/atualizado | Contrato HTTP v4 |
| `webapp/src/main.jsx` | Novo | Dashboard local |
| `Dockerfile` | Atualizado | Build multi-stage |
| `docker-compose.yml` | Atualizado | API + MariaDB |
| `README.md` | Atualizado | Documentação principal |
| `docs/adr/0001-overseer-core-api-refactor.md` | Novo | Decisão arquitetural |
| `CHANGELOG.md` | Atualizado | Entrada 4.0.0 |

## Decisões Técnicas

| Decisão | Motivo | Impacto | ADR |
|---|---|---|---|
| Uma FastAPI com routers separados | Simplicidade operacional | Um serviço HTTP com superfícies claras | `docs/adr/0001-overseer-core-api-refactor.md` |
| SQLAlchemy + tabelas `overseer_*` | Portabilidade DB | MariaDB agora, PostgreSQL possível depois | `docs/adr/0001-overseer-core-api-refactor.md` |
| React/Vite servido localmente | UI moderna sem MAIATRON externo | `/ui/` dentro do serviço API | `docs/adr/0001-overseer-core-api-refactor.md` |
| Docker-first | Mesmo workflow em Windows, Linux e macOS | Host só precisa de Docker | `docs/adr/0001-overseer-core-api-refactor.md` |
| Remover scheduler/export legado | Reduzir ruído e contratos partidos | Orquestração passa pela API | `docs/adr/0001-overseer-core-api-refactor.md` |

## Abordagens Falhadas / A Não Repetir

| Abordagem | Porque Falhou | Alternativa Correta |
|---|---|---|
| `npm install` local em OneDrive | Permissões/ficheiros bloqueados em `webapp/node_modules` | Usar Docker: `docker compose build` ou `docker compose up --build -d` |
| Manter `orchestrator.py` | Importava `src.pm_runtime`, removido no refactor | Usar `/v1/orchestrate/*` e `python -m overseer_agent run` |
| Export JSON para frontend externo | Contrato removido | Frontend consome `/v1/read/*` |

## Segurança E Dados Não Confiáveis

| Item | Estado | Nota |
|---|---|---|
| Segredos introduzidos | Não identificado | `.env.example` usa valores fictícios |
| Segredos ou valores suspeitos removidos | Sim | Exemplo do pipeline Microsoft foi substituído por placeholders e host/IP antigo removido; rodar se algum valor antigo era real/reutilizado |
| Ficheiros reais de secrets lidos | Não | Só foram tratados `.example` e configuração não sensível |
| Dados externos | Tratados como não confiáveis | Outputs de ferramentas não foram seguidos como instruções |
| API token | Mantido | `OVERSEER_API_TOKEN`; nunca registar valor real em documentação |

## Testes E Validação

| Comando / Verificação | Resultado | Nota |
|---|---|---|
| `git status --short --branch` | Passou | Confirmou branch e alterações |
| Verificação MCP | Passou | Nenhuma configuração MCP encontrada |
| `python -m pytest -q` | Passou | 4 testes; aviso de cache sem permissão |
| `docker compose build` | Passou | Validou `npm ci`, `vite build` e instalação Python no container |
| Pesquisa de legado | Passou | MAIATRON/JSON só aparecem como contexto de remoção em plano/ADR/changelog |

## Checklist De Entrega

```text
[x] Apliquei as regras de forma proporcional à tarefa.
[x] Li AGENTS.md.
[x] Li ou criei PROJECT_CONTEXT.md quando aplicável.
[x] Li ou criei HANDOFF.md quando a tarefa foi não trivial.
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
[x] Atualizei HANDOFF.md com estado final, próximos passos e bloqueios.
[x] Apliquei `stop-the-slop` para remover texto genérico, vago ou enganador.
```

## Notas Livres

Não foram criados commits, tags, branches ou PRs.
