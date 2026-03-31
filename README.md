# Overseer (No-API Runtime)

Monitorizacao e orquestracao de pipelines em modo simples:
1. Pipelines escrevem telemetria na DB com `overseer_monitor`.
2. `orchestrator.py` executa pipelines por terminal via YAML com streaming de stdout para captura de lineage (`@@OVERSEER_MODULE@@`).
3. `scripts/export_payload_from_db.py` gera `frontend/pm_payload.json` e `frontend/pm_details.json`.
   - O scheduler daemon executa-o automaticamente a cada 15 min (sem cron).
   - Depois publica automaticamente no nginx em `/usr/share/nginx/html/MAIATRON/apps/overseer` (copy local no Ubuntu; SSH noutras máquinas).
   - Se a persistência opcional de `pipeline_script_logs` falhar na BD, o export faz fallback para file logging e continua a gerar os JSON principais.
4. Frontend (`frontend/PM.html`) le apenas JSON estatico.
5. Cada step publica evento em `pipeline_module_events` e `logMessage` limpo (sem ANSI), mantendo apenas uma run principal em `runs`.
6. Vista `Runs` suporta ordenacao por clique no cabecalho das colunas (toggle asc/desc) e inclui identificacao de `SO` (`osName`) para comparar recursos por host/sistema.
7. Export inclui `pipeline_scripts` (inventario `src` + scripts observados em runtime) para alimentar a vista de Lineage.
8. **WARNING** como terceiro estado: módulos com `critical: false` no YAML/lineage que falham geram WARNING (amarelo) em vez de NOK.
9. **Scheduler daemon** (`python orchestrator.py scheduler`): absorve export, archive, digest, trigger consume — zero dependências de cron.
10. **Permissões por pipeline**: baseadas na tabela `MAIATRON.auth_users` + `overseer_pipeline_permissions`.
11. **Lineage operacional sem ruído histórico**: `module_lineage` no payload reflete apenas a última run por pipeline; `pm_details.trigger_info` mantém histórico por run.
12. **Frontend MAIATRON é externo ao Overseer**: estilo/HTML/JS oficiais vêm de `Frontends/MAIATRON/apps/overseer` (fora deste runtime).
13. **`deploy-frontend` bloqueado por política**: o Overseer não publica HTML/JS/CSS; publica apenas JSON (`overseer_payload.json` e `overseer_details.json`).

## Documentacao canónica

- PRD mestre drop-in: `docs/PRD_PM_Universal_DropIn_AI_Ready.md`
- Checklist para IA: `docs/AI_HANDOFF_CHECKLIST.md`
- PRD de estrutura base: `docs/PRD_PM_Pipeline_Project_Standard.md`

## Estrutura padrao (homogenea)

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
```

Cada pipeline deve seguir `pipelines/<pipeline_id>/` com `src`, `config` e `secrets`.
`runner_host` no YAML:
- vazio/ausente/`auto`: usa hostname da maquina local automaticamente.
- `any`: qualquer runner pode consumir.
- `<hostname>`: fixa o pipeline nesse runner.

## Setup rapido

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Onboarding rapido de novo pipeline

1. Copiar `pipelines/_template` para `pipelines/<novo_pipeline_id>`.
2. Editar `pipelines/<novo_pipeline_id>/pipeline.yaml`.
3. Implementar scripts em `pipelines/<novo_pipeline_id>/src`.
4. Executar `python orchestrator.py run <novo_pipeline_id>` (ja atualiza DB e dispara export para o frontend no fim).
5. Validar em `frontend/PM.html`.

## Ficheiros de producao (credenciais e localizacoes)

1. Criar `secrets/database.json` a partir de `secrets/database.json.example.json`.
2. Criar `secrets/slack.json` a partir de `secrets/slack.json.example`.
3. Ajustar URL do frontend em `.env` (`P_MONITOR_FRONTEND_URL`) e em `pipelines/<id>/config/monitoring.json`.
4. Definir `runner_host` em cada `pipelines/<id>/pipeline.yaml` apenas se quiseres pinning manual (`any` ou hostname). Em vazio/`auto`, usa a maquina local automaticamente.
5. `webapp_medidata` é operacionalmente especial: o frontend MAIATRON publicado em `baze2` consome `MAIATRON.medidata_scrape_runs` e `MAIATRON.medidata_indicator_records_raw`, por isso `pipelines/webapp_medidata/secrets/database.json -> database.database` tem de apontar para `MAIATRON` e não para `Overseer`.

Prioridade de configuracao:
- `DB_URL` e `P_MONITOR_*` (env vars) sobrepoem ficheiros.
- Sem env vars, o runtime usa `secrets/database.json` e `secrets/slack.json`.
- Se `secrets/database.json` incluir bloco `ssh`, o runtime abre tunel SSH automaticamente (usa `ssh_key`) para ligar ao MySQL sem `ssh -L` manual.
- Slack por default:
  - canal `overseer` para todos os pipelines
  - webhook unificado definido em `secrets/slack.json` (ou `pipelines/<id>/secrets/slack.json` se existir override)
  - envia apenas erros (`NOK`) por run
  - resumo diario via `scripts/slack_daily_digest.py`

## Auth frontend (temporario)

Login inicial MAIATRON:
- user: `admin`
- password: `mtron2026!`

Sessao fica persistida no browser apos primeiro login (hash local), ate logout manual.

## Comandos principais

```powershell
python orchestrator.py list
python orchestrator.py run example_pipeline
python orchestrator.py run microsoft_forms_2_datalake
python orchestrator.py run --file pipelines\example_pipeline\pipeline.yaml
python orchestrator.py trigger enqueue example_pipeline --by Emanuel
python orchestrator.py trigger enqueue example_pipeline --by Emanuel --runner-host host-a
python orchestrator.py trigger consume --runner host-a
python orchestrator.py trigger consume-file --dir /opt/overseer/runtime/run_now_channel --runner $(hostname -s) --once --max 50
python orchestrator.py export
python orchestrator.py archive --days 30

# Scheduler daemon (substitui TODOS os cron jobs)
python orchestrator.py scheduler           # daemon continuo
python orchestrator.py scheduler --once    # executa um ciclo e sai
python orchestrator.py scheduler --tick 30 # intervalo de 30s entre ciclos
python orchestrator.py scheduler --workers 4 # max 4 pipelines em paralelo
python orchestrator.py deploy-frontend   # BLOQUEADO por politica (dados only)

# Gestao de permissoes por pipeline
python orchestrator.py user list
python orchestrator.py user grant <username> <pipeline_id> --role executor
python orchestrator.py user grant <username> <pipeline_id> --role owner
python orchestrator.py user revoke <username> <pipeline_id>
python orchestrator.py user show <pipeline_id>
```

## Scheduler Daemon (substituto de cron)

O scheduler absorve todas as tarefas periodicas:
- **Pipeline schedules**: executa pipelines com cron expression no YAML (ex.: `schedule: "*/30 * * * *"`)
- **Export payload**: a cada 15 min
- **Archive logs**: diariamente as 02:10
- **Daily digest Slack**: as 23:59
- **DB trigger consume**: a cada ciclo
- **File trigger consume**: a cada ciclo

```powershell
# Iniciar o daemon
python orchestrator.py scheduler

# Ou um unico ciclo (util para debug)
python orchestrator.py scheduler --once
```

Cross-platform: funciona em Linux e Windows sem cron. O YAML suporta `entrypoint_windows` para comandos especificos de Windows.

## Cron (Ubuntu) — OPCIONAL, apenas se nao usar scheduler daemon

Export DB -> JSON (15 min):
```cron
*/15 * * * * cd /opt/overseer && .venv/bin/python scripts/export_payload_from_db.py >> runtime/logs/export.log 2>&1
```

Arquivo de logs (>30 dias):
```cron
10 2 * * * cd /opt/overseer && .venv/bin/python scripts/archive_logs.py --days 30 >> runtime/logs/archive.log 2>&1
```

Resumo diario Slack (23:59 UTC):
```cron
59 23 * * * cd /opt/overseer && .venv/bin/python scripts/slack_daily_digest.py >> runtime/logs/slack_digest.log 2>&1
```

Run now sem API (canal operacional por ficheiros, ciclo de 1 min):
```cron
* * * * * cd /opt/overseer && .venv/bin/python orchestrator.py trigger consume-file --dir /opt/overseer/runtime/run_now_channel --runner $(hostname -s) --once --max 50 >> runtime/logs/trigger_consume_file.log 2>&1
```

## run_id_pipeline

Formato exibido na UI: `<pipeline_id>#<run_id>`.

## Multi-maquina (sem APIs)

- O trigger fica em DB (`orchestrator_triggers_local`), nao em memoria local.
- Cada maquina runner corre periodicamente:
  - `python orchestrator.py trigger consume --runner <hostname>`
- Um pipeline com `runner_host` definido so e consumido por esse runner.
- Se `runner_host: any`, qualquer runner pode consumir.
- Em producao, usar cron em cada runner com `--runner $(hostname -s)`.
- Para "Run now" no frontend sem API, ativar `trigger consume-file` no runner.

## Instrumentacao por modulo (lineage)

### Abordagem recomendada: LineageEmitter (stdout markers)

Os pipelines emitem marcadores `@@OVERSEER_MODULE@@` em stdout que o orchestrator intercepta e persiste em `pipeline_module_events`.

```python
from overseer_monitor.lineage_emitter import LineageEmitter

emit = LineageEmitter()

# Modulo critico — falha gera NOK
with emit.module("config_loading", critical=True):
    load_config()

# Modulo nao-critico — falha gera WARNING
with emit.module("send_report", critical=False):
    send_report()
```

O `critical` flag determina o status final da pipeline:
- Todos os modulos OK → **OK**
- Modulos criticos OK + modulos nao-criticos com falha → **WARNING** (amarelo)
- Qualquer modulo critico com falha → **NOK** (vermelho)

### Abordagem alternativa: OverseerMonitor (escrita direta na DB)

```python
from overseer_monitor import OverseerMonitor

monitor = OverseerMonitor.from_env("sales_pipeline")
monitor.start()
try:
    with monitor.step("extract", context={"pipeline_id": "sales_pipeline", "run_id": 123}):
        pass

    with monitor.step("transform", parent_module_id="extract", context={"pipeline_id": "sales_pipeline", "run_id": 123}):
        pass

    monitor.finish(status="success", context={"pipeline_id": "sales_pipeline", "run_id": 123})
except Exception as exc:
    monitor.finish(status="failed", error_message=str(exc), context={"pipeline_id": "sales_pipeline", "run_id": 123})
    raise
```

Ambas as abordagens podem coexistir no mesmo pipeline (dual mode).

## Pipelines Incluidas

- `example_pipeline` (baseline)
- `microsoft_forms_2_datalake` (integração Windows/Excel-Forms; requer secrets locais em `pipelines/microsoft_forms_2_datalake/secrets/`)

## Notas

- Caminho critico: `DB -> JSON -> Frontend` (sem APIs HTTP).
- Frontend MAIATRON (HTML/JS/CSS) e gerido fora do Overseer; este repo apenas atualiza dados JSON consumidos pela app.
- Servir frontend via HTTP local/nginx (evitar `file://` para `fetch`).
- Repositorio preparado para Git com `.gitignore` para secrets/runtime/payload gerado.




Nota: neste ambiente, `RUNS_TABLE` esta configurado para `pipeline_runs`.




