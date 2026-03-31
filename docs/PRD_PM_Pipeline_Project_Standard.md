# PRD - Projeto de Pipelines com Overseer (Padrao Homogeneo)

## 1. Objetivo
Definir um padrao unico para qualquer projeto de pipeline usar o `Overseer` com:
- orquestracao CLI simples,
- telemetria em DB via `overseer_monitor`,
- frontend estatico alimentado por JSON gerado da DB.

## 2. Arquitetura alvo
1. Pipeline executa scripts internos (`src/`) e chama `overseer_monitor`.
2. `overseer_monitor` grava logs e eventos de modulo na DB (`logs`, `pipeline_module_events`).
3. `scripts/export_payload_from_db.py` gera `frontend/pm_payload.json` e `frontend/pm_details.json` (15 min).
4. Frontend (`frontend/PM.html`) le JSON e mostra Kiosk, Dashboard, Pipelines, Runs, Insights e Lineage.
5. `scripts/archive_logs.py` move logs >30 dias para `logs_archive`.

## 3. Estrutura obrigatoria por pipeline
Cada pipeline no repositorio deve seguir:

```text
pipelines/<pipeline_id>/
  pipeline.yaml
  src/
    main.py
    ...
  config/
    monitoring.json (opcional)
    *.json
  secrets/
    (nao versionar credenciais reais)
```

Regras:
- `pipeline_id` da pasta e do YAML devem coincidir.
- `entrypoint` do YAML executa dentro desta pasta.
- `secrets/` e para ficheiros locais; no git manter apenas `.example`/`.gitkeep`.

## 4. Contrato do YAML (`pipeline.yaml`)
Campos obrigatorios:
- `pipeline_id` (string unica)
- `name` (string)
- `owner` (string)
- `criticality` (`low|medium|high|critical`)
- `timeout_sec` (int, default 3600)
- `retries` (int, default 2)
- `entrypoint` (comando shell) ou `steps` (lista DAG simples)

Campos opcionais:
- `schedule` (metadado cron/manual)
- `runner_host` (hostname do runner alvo; `auto`/vazio usa a maquina local; `any` permite qualquer maquina)

## 5. Contrato do `overseer_monitor`
API canonica:
- `OverseerMonitor(script_name, table_name='logs', db_params=None, frontend_base_url=None, slack_config=None, extra_tags=None)`
- `start()`
- `finish(status='success', error_message=None, context=None)`
- `step(module_id, parent_module_id=None, context=None)`

Contexto recomendado em `finish/step`:
- `pipeline_id`
- `run_id`
- `attempt_id` (quando aplicavel)
- `trigger_type` (`manual|trigger_file|scheduled`)
- `runner_host` (hostname do runner que executou)

## 6. Contrato de dados DB
Tabela `logs` (minimo):
- `id`, `scriptName`, `startDate`, `endDate`, `execTime`, `usageCPU`, `usageMemoria`, `status`, `errorMessage`, `hostname`, `pipelineId`, `runId`, `attemptId`, `triggerType`, `regDate`.

Tabela `pipeline_module_events`:
- `event_id`, `pipelineId`, `runId`, `moduleId`, `parentModuleId`, `status`, `startedAt`, `endedAt`, `durationSec`, `errorMessage`, `hostname`, `triggerType`, `contextJson`, `regDate`.

Tabela `logs_archive`:
- estrutura de `logs` + `archived_at`, `archive_batch_id`.

Tabela `orchestrator_triggers_local`:
- fila de triggers multi-maquina (`queued|claimed|consumed|failed`), com `runner_host`, `claimed_by`, `claimed_at`, `consumed_at`.

Tabela `orchestrator_runs_local`:
- historico de execucoes com `runner_host` para auditoria de onde correu.

## 7. Operacao standard
### 7.1 Execucao manual
1. `python orchestrator.py list`
2. `python orchestrator.py run <pipeline_id>`

### 7.2 Trigger via DB (multi-maquina)
1. Frontend/operador enfileira trigger: `python orchestrator.py trigger enqueue <pipeline_id> --by <user> [--runner-host host-a]`.
2. Cada maquina runner consome: `python orchestrator.py trigger consume --runner <hostname>`.
3. O consumo respeita `runner_host` do trigger e do YAML do pipeline.

### 7.3 Run now sem API (canal por ficheiros)
1. Frontend aciona `Run now` e gera trigger no canal operacional local.
2. Runner consome com: `python orchestrator.py trigger consume-file --dir /opt/overseer/runtime/run_now_channel --runner <hostname> --once --max 50`.
3. Triggers processadas ficam auditáveis em `done/failed`.

### 7.4 Export
- `python scripts/export_payload_from_db.py`
- cron fixo: cada 15 minutos.

### 7.5 Arquivo
- `python scripts/archive_logs.py --days 30`
- cron diario recomendado.

## 8. UI e entendimento de utilizador
A UI deve exibir:
- `run_id_pipeline` no formato `<pipeline_id>#<run_id>` em Runs e detalhe.
- explicacao de metricas com labels/tooltips:
  - `success_rate`: percentagem de runs OK na janela.
  - `stale`: pipeline sem run recente vs cadencia esperada.
  - `regression`: degradacao de erro/performance vs janela anterior.
  - `riskScore`: score operacional para priorizacao.

## 9. Seguranca e boas praticas
- Nao guardar segredos reais no git.
- Separar `config` (nao sensivel) de `secrets` (sensivel).
- Usar variaveis de ambiente para DB/Slack em producao.
- Auth no frontend e temporario; tratar como conveniencia, nao como controlo forte.
- Ficheiros obrigatorios em producao:
  - `secrets/database.json`
  - `secrets/slack.json`
  - `pipelines/<pipeline_id>/pipeline.yaml` com `runner_host` quando aplicavel

## 10. Critérios de aceitação
1. Pipeline novo adicionado com a estrutura padrao executa via `orchestrator.py run`.
2. Run grava em `logs` e eventos por modulo em `pipeline_module_events`.
3. Export gera payload valido com `run_id_pipeline` e `module_lineage`.
4. Frontend carrega sem APIs e apresenta dados atualizados no ciclo de 15 min.
5. Arquivo move dados >30 dias para `logs_archive` sem perda.




