# Changelog
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




