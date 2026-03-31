# PRD Mestre: Overseer Universal (AI-Ready / Drop-in)

## 1. Objetivo
Permitir que qualquer projeto de pipeline integre o `Overseer` sem ambiguidade, com:
- orquestração CLI;
- telemetria padrão (`logs` + `pipeline_module_events`);
- export DB -> JSON para frontend estático;
- documentação suficiente para execução por humano ou IA sem decisões adicionais.

## 2. Escopo
### In scope
- Runtime sem APIs HTTP no caminho crítico.
- Pipeline config por `YAML`.
- Trigger queue em DB para multi-maquina.
- Canal run-now sem API por ficheiros (opcional, recomendado para UX imediata).
- Export fixo de 15 em 15 minutos.
- Arquivo automático de logs > 30 dias.
- Estrutura homogénea de pastas por pipeline.
- Suporte a runners Windows para pipelines com entrypoint Python local (ex.: Excel/Forms).

### Out of scope
- OIDC/SSO forte no frontend.
- Scheduling distribuído avançado (cluster manager).
- Observability stack externa (Prometheus/Grafana/ELK).

## 3. Arquitetura canónica
1. Runner executa pipeline via `orchestrator.py`.
2. Pipeline usa `overseer_monitor` para `start()/step()/finish()`.
3. `overseer_monitor` grava em `logs` e `pipeline_module_events`.
4. `scripts/export_payload_from_db.py` gera `frontend/pm_payload.json` + `frontend/pm_details.json` (por cron e automaticamente no fim de `orchestrator.py run`), incluindo `pipeline_scripts` para lineage baseado em inventario+runtime.
   - Semântica atual de lineage: `module_lineage` representa apenas a última run observada de cada pipeline (sem mistura de módulos históricos de runs antigas).
   - `pm_details.trigger_info` mantém contexto por `run_id` para histórico operacional.
   - Se a escrita opcional em `pipeline_script_logs` falhar, o export deve degradar para file logging sem bloquear a geração dos JSON principais.
   - Exceção operacional conhecida: `webapp_medidata` publica dados para uma app MAIATRON externa que lê tabelas `medidata_*` no schema `MAIATRON` do `baze2`; esse pipeline não deve apontar os dados da app ao schema `Overseer`.
5. `frontend/PM.html` (ou app MAIATRON equivalente) lê JSON e apresenta operação.
   - O Overseer não é fonte de verdade para estilo/frontend assets; HTML/JS/CSS MAIATRON são geridos externamente.
6. `scripts/archive_logs.py` move histórico para `logs_archive`.

## 4. Estrutura obrigatória do repositório
```text
Overseer/
  frontend/
    PM.html
    pm.css
    pm.js
    pm_payload.json
    pm_details.json
  orchestrator.py
  scripts/
    export_payload_from_db.py
    archive_logs.py
    crontab.example
  overseer_monitor/
  pipelines/
    _template/
      pipeline.yaml
      src/
      config/
      secrets/
    <pipeline_id>/
      pipeline.yaml
      src/
      config/
      secrets/
  config/
  secrets/
  runtime/
  README.md
  CHANGELOG.md
  .gitignore
```

## 5. Contrato de pipeline (`pipelines/<id>/pipeline.yaml`)
Campos obrigatórios:
- `pipeline_id`
- `name`
- `owner`
- `criticality` (`low|medium|high|critical`)
- `timeout_sec` (default 3600)
- `retries` (default 2)
- `entrypoint` ou `steps`

Campos opcionais:
- `schedule`
- `runner_host`

Regras `runner_host`:
- vazio/ausente/`auto`: resolve para hostname local.
- `any`: qualquer runner pode consumir.
- `<hostname>`: fixo nessa máquina.

## 6. Contratos de dados DB
Tabela `logs` (mínimo):
- `id`, `scriptName`, `startDate`, `endDate`, `execTime`, `usageCPU`, `usageMemoria`, `status`, `errorMessage`, `logMessage`, `hostname`, `osName`, `osRelease`, `osPlatform`, `pipelineId`, `runId`, `attemptId`, `triggerType`, `owner`, `criticality`, `regDate`.

Tabela `pipeline_module_events`:
- `event_id`, `pipelineId`, `runId`, `moduleId`, `parentModuleId`, `status`, `startedAt`, `endedAt`, `durationSec`, `errorMessage`, `logMessage`, `hostname`, `triggerType`, `contextJson`, `regDate`.

Tabela `orchestrator_triggers_local`:
- fila multi-maquina com estados `queued|claimed|consumed|failed`.

Tabela `orchestrator_runs_local`:
- auditoria de execução, incluindo `runner_host`.

Tabela `logs_archive`:
- espelho de `logs` + `archived_at`, `archive_batch_id`.

## 7. Contrato do módulo `overseer_monitor`
API:
- `OverseerMonitor(...)`
- `start()`
- `finish(status='success', error_message=None, context=None)`
- `step(module_id, parent_module_id=None, context=None)`

Garantias:
- normaliza status para `OK|NOK`;
- tolera falha parcial de DB/Slack sem quebrar pipeline;
- grava hostname e metadados de contexto.
- persiste `logMessage` (stdout/stderr) sem códigos ANSI para leitura no modal.
- mantém uma run principal em `logs/runs`, com detalhe por step em `pipeline_module_events`.
- notificação Slack por run apenas para `NOK` (default).

## 8. Configuração de produção
Ficheiros obrigatórios:
- `secrets/database.json`
- `secrets/slack.json`
- `config/auth.local.json` (enquanto auth temporário existir)

Opcional em `secrets/database.json`:
- bloco `ssh` com `host`, `port`, `user`, `key_filename`, `remote_bind_host`, `remote_bind_port`.
- Quando presente, o runtime abre tunel SSH automaticamente para acesso DB.

Prioridade de configuração:
1. env vars (`DB_URL`, `P_MONITOR_*`)
2. `secrets/database.json` e `secrets/slack.json`

Padrão de Slack (produção):
- canal alvo único: `overseer`;
- webhook unificado para todos os pipelines (com override por pipeline apenas quando estritamente necessário).

## 9. Operação diária
Comandos:
- `python orchestrator.py list`
- `python orchestrator.py run <pipeline_id>` (inclui export automatico no fim)
- `python orchestrator.py trigger enqueue <pipeline_id> --by <user> [--runner-host <host>]`
- `python orchestrator.py trigger consume --runner <hostname> --max 20`
- `python orchestrator.py trigger consume-file --dir /opt/overseer/runtime/run_now_channel --runner <hostname> --once --max 50`
- `python scripts/export_payload_from_db.py`
- `python scripts/archive_logs.py --days 30`
- `python scripts/slack_daily_digest.py`
- `python orchestrator.py deploy-frontend` (bloqueado por política MAIATRON; não deve ser usado para publicar HTML/JS/CSS)

Cron mínimo:
- export: `*/15 * * * * ... export_payload_from_db.py`
- arquivo: `10 2 * * * ... archive_logs.py --days 30`
- consume: `* * * * * ... orchestrator.py trigger consume --runner $(hostname -s) --max 20`
- run-now channel: `* * * * * ... orchestrator.py trigger consume-file --dir /opt/overseer/runtime/run_now_channel --runner $(hostname -s) --once --max 50`
- digest Slack: `59 23 * * * ... slack_daily_digest.py`

## 10. Onboarding drop-in de um novo pipeline
1. Copiar `pipelines/_template` para `pipelines/<novo_id>`.
2. Ajustar `pipeline.yaml` (IDs, owner, entrypoint, runner_host).
3. Implementar scripts em `pipelines/<novo_id>/src`.
4. Preencher `pipelines/<novo_id>/secrets` localmente (não versionar).
5. Executar `python orchestrator.py run <novo_id>` (DB + export frontend).
6. Validar frontend em `frontend/PM.html`.
7. Configurar cron no runner.

## 11. Critérios de aceitação
1. Pipeline novo executa sem alterar core do monitor.
2. Run aparece em `logs` com `hostname`.
3. Eventos de módulo aparecem em `pipeline_module_events`.
4. Export produz JSON válido em `frontend/`.
5. UI mostra runs com ordenacao por cabecalho (asc/desc) e lineage no proximo ciclo.
   - Lineage mostra módulos da última run por pipeline (sem ruído histórico).
6. Arquivo move dados >30 dias com auditoria.

## 12. Entregáveis para qualquer IA operar sem contexto extra
Obrigatórios no repositório:
- `README.md` com quickstart.
- `CHANGELOG.md` atualizado.
- este PRD mestre.
- `pipelines/_template` completo.
- `.gitignore` com proteção de secrets/runtime.




