const by = (selector, root = document) => Array.from(root.querySelectorAll(selector));
const one = (selector, root = document) => root.querySelector(selector);

const state = {
  overview: null,
  database: null,
  pipelines: [],
  allRuns: [],
  hostFilter: 'all',
  selectedDeploymentKey: sessionStorage.getItem('overseer_selected_deployment') || '',
  selectedNodeId: '',
  selectedPipeline: null,
  runnerHosts: null,
};

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));
}

function apiToken() {
  const fromConfig = window.OVERSEER_CONFIG?.apiToken;
  if (fromConfig) return String(fromConfig);
  return sessionStorage.getItem('overseer_api_token') || '';
}

async function api(path) {
  const headers = { Accept: 'application/json' };
  if (apiToken()) headers.Authorization = `Bearer ${apiToken()}`;
  const response = await fetch(path, { headers });
  if (response.status === 401) throw new Error('API devolveu 401. Confirma o token.');
  if (!response.ok) throw new Error(`API devolveu HTTP ${response.status}.`);
  return response.json();
}

function effectiveHostId(item) {
  if (!item) return '';
  const explicit = String(item.host_id || '').trim();
  if (explicit && explicit.toLowerCase() !== 'any') return explicit;
  const metaHost = String(item.metadata?.host_id || '').trim();
  if (metaHost) return metaHost;
  const legacy = String(item.pipeline_id || '').includes('__')
    ? String(item.pipeline_id).split('__').pop()
    : '';
  if (legacy) return legacy;
  return '';
}

function hostKeyMatch(left, right) {
  return String(left || '').trim().toUpperCase() === String(right || '').trim().toUpperCase();
}

function findPipelineRow(pipelineId, hostId) {
  const logicalId = logicalPipelineId(pipelineId);
  const hostKey = String(hostId || '').trim();
  return (state.pipelines || []).find((item) => (
    logicalPipelineId(item.pipeline_id) === logicalId
    && hostKeyMatch(effectiveHostId(item), hostKey)
  )) || null;
}

function pipelineLabel(source, pipelineId = '', hostId = '') {
  const row = typeof source === 'object' && source
    ? source
    : findPipelineRow(pipelineId, hostId);
  const id = logicalPipelineId(
    source?.pipeline_id || pipelineId || row?.pipeline_id || '',
  );
  const title = source?.pipeline_name || source?.name || row?.name || id || '--';
  const subtitle = id && id !== title ? id : '';
  return { title, subtitle, id };
}

function pipelineLabelHtml(label, hostId = '') {
  const host = String(hostId || '').trim();
  const hostSuffix = host ? ` @ ${esc(host)}` : '';
  const sub = label.subtitle
    ? `<span class="mono pipeline-sub">${esc(label.subtitle)}${hostSuffix}</span>`
    : (host ? `<span class="mono pipeline-sub">${esc(host)}</span>` : '');
  return `<span class="pipeline-label"><strong>${esc(label.title)}</strong>${sub}</span>`;
}

function criticalityClass(value) {
  const raw = String(value || '').toLowerCase();
  if (raw === 'critical' || raw === 'high') return 'danger';
  if (raw === 'low') return 'ok';
  return 'warn';
}

function updateTokenBanner() {
  const banner = one('[data-token-banner]');
  if (!banner) return;
  banner.hidden = Boolean(apiToken());
}

function renderDeploymentRuns(item) {
  if (!item) {
    html('[data-recent-runs]', emptyBlock('Selecciona um pipeline na tabela.'));
    return;
  }
  const key = deploymentKey(item);
  const runs = (state.allRuns || [])
    .filter((run) => runDeploymentKey(run) === key)
    .sort((a, b) => new Date(b.started_at) - new Date(a.started_at))
    .slice(0, 8);
  const runsUrl = `run-detail.html?${new URLSearchParams({
    pipeline: item.pipeline_id,
    host: effectiveHostId(item),
  }).toString()}`;
  const head = `<div class="inspector-runs-head"><a class="btn" href="${esc(runsUrl)}">Ver todas as runs</a></div>`;
  html('[data-recent-runs]', head + (runs.length ? runs.map((run) => {
    const stale = isStaleRun(run.started_at, run.status, false, item.schedule);
    const klass = stale ? 'stale' : statusClass(run.status);
    return `
    <a class="alert-item alert-link" href="${esc(runDetailUrl(run))}">
      <div><strong>${esc(run.run_id)}</strong><p>${esc(formatDate(run.started_at))} · ${esc(duration(run.duration_sec))}</p></div>
      <span class="pill ${klass}">${esc(stale ? 'stale' : statusLabel(run.status))}</span>
    </a>`;
  }).join('') : emptyBlock('Sem runs para este deployment.')));
}

function setInspectorSelection(item) {
  state.selectedPipeline = item;
  const inspector = one('#inspector');
  if (!inspector || !item) return;
  text('[data-inspector-title]', `${pipelineDisplayName(item)} · ${hostDisplay(item)}`, inspector);
  text('[data-inspector-state]', statusLabel(item.last_status), inspector);
  const copy = one('[data-copy]', inspector);
  if (copy) copy.dataset.copy = item.last_run_id || '';
  const dagLink = one('[data-inspector-dag]', inspector);
  if (dagLink) {
    dagLink.hidden = !item.pipeline_id;
    dagLink.href = lineageUrl(item.pipeline_id, effectiveHostId(item));
  }
  renderDeploymentRuns(item);
}

function bindHostFilters() {
  const container = one('[data-host-filters]');
  if (!container) return;
  const hosts = [...new Set((state.pipelines || []).map((item) => effectiveHostId(item)).filter(Boolean))].sort();
  const chips = [{ id: 'all', label: 'Todos' }, ...hosts.map((host) => ({ id: host, label: host }))];
  container.innerHTML = chips.map((chip) => `
    <button type="button" class="host-chip${state.hostFilter === chip.id ? ' is-active' : ''}" data-host-filter="${esc(chip.id)}">${esc(chip.label)}</button>
  `).join('');
  by('[data-host-filter]', container).forEach((button) => {
    button.addEventListener('click', () => {
      state.hostFilter = button.dataset.hostFilter || 'all';
      applyPipelineFilters();
      bindHostFilters();
    });
  });
}

function applyPipelineFilters() {
  const table = one('#pipeline-table');
  if (!table) return;
  const stateFilter = one('[data-filter="#pipeline-table"]')?.value || 'all';
  const query = one('[data-search="#pipeline-table"]')?.value.trim().toLowerCase() || '';
  by('tbody tr[data-name]', table).forEach((row) => {
    const hostOk = state.hostFilter === 'all' || hostKeyMatch(row.dataset.host, state.hostFilter);
    const stateOk = stateFilter === 'all' || row.dataset.state === stateFilter;
    const searchOk = !query || row.textContent.toLowerCase().includes(query);
    row.hidden = !(hostOk && stateOk && searchOk);
  });
}

function bindKpiActions() {
  one('[data-kpi-action="scroll-pipelines"]')?.addEventListener('click', () => {
    one('#pipelines-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
  one('[data-kpi-action="filter-failed"]')?.addEventListener('click', () => {
    const control = one('[data-filter="#pipeline-table"]');
    if (control) {
      control.value = 'danger';
      control.dispatchEvent(new Event('change'));
    }
    one('#pipelines-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
}

function text(selector, value, root = document) {
  const target = one(selector, root);
  if (target) target.textContent = value;
}

function html(selector, value, root = document) {
  const target = one(selector, root);
  if (target) target.innerHTML = value;
}

function setAlert(message = '', type = '') {
  html('[data-alert]', message ? `<div class="alert ${esc(type)}">${esc(message)}</div>` : '');
}

function setSync(label, kind = '') {
  const target = one('[data-sync-state]');
  if (!target) return;
  target.className = `pill ${kind}`.trim();
  target.textContent = label;
}

function statusClass(status) {
  const raw = String(status || '').toLowerCase();
  if (['ok', 'success', 'done', 'completed', 'ready'].includes(raw)) return 'ok';
  if (['warning', 'warn', 'queued', 'running', 'claimed', 'late'].includes(raw)) return 'warn';
  if (!raw) return '';
  return 'danger';
}

function stateBucket(status) {
  const klass = statusClass(status);
  if (klass === 'ok') return 'ok';
  if (klass === 'warn') return 'warn';
  if (klass === 'danger') return 'danger';
  return 'all';
}

function statusLabel(status) {
  return status || 'sem estado';
}

function formatDate(value) {
  if (!value) return '--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function duration(value) {
  if (value === null || value === undefined || value === '') return '--';
  const seconds = Number(value);
  if (!Number.isFinite(seconds)) return String(value);
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

function logicalPipelineId(pipelineId) {
  const raw = String(pipelineId || '');
  const idx = raw.lastIndexOf('__');
  if (idx > 0) {
    const host = raw.slice(idx + 2);
    if (host) return raw.slice(0, idx);
  }
  return raw;
}

function normalizePipelineRow(item) {
  const logicalId = logicalPipelineId(item?.pipeline_id);
  if (!logicalId) return null;
  const candidate = { ...item, pipeline_id: logicalId };
  const host = effectiveHostId(candidate);
  if (host) candidate.host_id = host;
  return candidate;
}

function dedupePipelines(pipelines) {
  return (pipelines || [])
    .map((item) => normalizePipelineRow(item))
    .filter((item) => item && effectiveHostId(item))
    .sort((left, right) => {
      const byPipeline = String(left.pipeline_id).localeCompare(String(right.pipeline_id));
      if (byPipeline !== 0) return byPipeline;
      return String(left.host_id || '').localeCompare(String(right.host_id || ''));
    });
}

function deploymentKey(item) {
  const logicalId = logicalPipelineId(item?.pipeline_id || item);
  const hostId = typeof item === 'object' ? (item.host_id || '') : '';
  return `${logicalId}::${hostId}`;
}

function runDeploymentKey(run) {
  return deploymentKey({ pipeline_id: run.pipeline_id, host_id: run.host_id || '' });
}

const NAV_ITEMS = [
  { id: 'dashboard', href: 'dashboard.html', label: 'Operações', hint: 'estado e KPIs' },
  { id: 'runs', href: 'run-detail.html', label: 'Runs', hint: 'histórico e detalhe' },
  { id: 'lineage', href: 'lineage.html', label: 'DAG', hint: 'catálogo e módulos' },
  { id: 'deployments', href: 'deployments.html', label: 'Ambiente', hint: 'DB, hosts e actividade' },
];

function renderAppNav(currentId) {
  const nav = one('[data-app-nav]');
  if (!nav) return;
  nav.innerHTML = NAV_ITEMS.map((item) => `
    <a href="${esc(item.href)}" ${item.id === currentId ? 'aria-current="page"' : ''} title="${esc(item.hint)}">
      <span class="nav-icon" aria-hidden="true">${esc(item.label.charAt(0))}</span>
      <span class="nav-copy"><strong>${esc(item.label)}</strong><small>${esc(item.hint)}</small></span>
    </a>
  `).join('');
}

function runDetailUrl(run) {
  const params = new URLSearchParams({ run: run.run_id });
  if (run.pipeline_id) params.set('pipeline', logicalPipelineId(run.pipeline_id));
  if (run.host_id) params.set('host', run.host_id);
  return `run-detail.html?${params.toString()}`;
}

function parseDeploymentKey(key) {
  const [pipelineId, hostId = ''] = String(key || '').split('::');
  return { pipelineId, hostId };
}

function pipelineDisplayName(item) {
  return pipelineLabel(item).title;
}

function hostDisplay(item) {
  const host = effectiveHostId(item);
  if (host) return host;
  return '--';
}

function isManualSchedule(schedule) {
  const normalized = String(schedule || 'manual').trim().toLowerCase();
  return !normalized || normalized === 'manual' || normalized === 'paused';
}

function isStaleRun(startedAt, status, deploymentStale = false, schedule = null) {
  if (isManualSchedule(schedule)) return false;
  if (deploymentStale) return true;
  if (String(status || '').toLowerCase() !== 'running' || !startedAt) return false;
  const date = new Date(startedAt);
  if (Number.isNaN(date.getTime())) return false;
  return Date.now() - date.getTime() > 24 * 60 * 60 * 1000;
}

function deploymentStaleFlag(item) {
  if (isManualSchedule(item?.schedule)) return false;
  return Boolean(item?.is_stale);
}

function deploymentShowsStale(item) {
  if (!item || isManualSchedule(item.schedule)) return false;
  return deploymentStaleFlag(item) || isStaleRun(item.last_started_at, item.last_status, false, item.schedule);
}

function lineageUrl(pipelineId, hostId) {
  const params = new URLSearchParams({ pipeline: pipelineId });
  if (hostId) params.set('host', hostId);
  return `lineage.html?${params.toString()}`;
}

function emptyRow(columns, label) {
  return `<tr><td colspan="${columns}"><span class="empty-state">${esc(label)}</span></td></tr>`;
}

function emptyBlock(label) {
  return `<div class="empty-state">${esc(label)}</div>`;
}

function bindChrome(refreshFn) {
  one('[data-refresh]')?.addEventListener('click', refreshFn);
}

function bindFilters() {
  by('[data-filter]').forEach((control) => {
    control.addEventListener('change', () => {
      if (control.dataset.filter === '#pipeline-table') {
        applyPipelineFilters();
        return;
      }
      const table = document.querySelector(control.dataset.filter);
      const value = control.value;
      if (!table) return;
      by('tbody tr', table).forEach((row) => {
        row.hidden = value !== 'all' && row.dataset.state !== value;
      });
    });
  });
}

function bindSearch() {
  by('[data-search]').forEach((input) => {
    input.addEventListener('input', () => {
      if (input.dataset.search === '#pipeline-table') {
        applyPipelineFilters();
        return;
      }
      const target = document.querySelector(input.dataset.search);
      const query = input.value.trim().toLowerCase();
      if (!target) return;
      by('[data-search-row]', target).forEach((row) => {
        row.hidden = query && !row.textContent.toLowerCase().includes(query);
      });
    });
  });
}

function bindCopy() {
  by('[data-copy]').forEach((button) => {
    button.addEventListener('click', async () => {
      const value = button.dataset.copy || '';
      if (!value) return;
      try {
        await navigator.clipboard.writeText(value);
        const original = button.textContent;
        button.textContent = 'Copiado';
        setTimeout(() => { button.textContent = original; }, 1200);
      } catch {
        button.textContent = value;
      }
    });
  });
}

function bindTabs() {
  by('[data-tab]').forEach((button) => {
    button.addEventListener('click', () => {
      const group = button.closest('[data-tabs]');
      by('[data-tab]', group).forEach((item) => item.classList.remove('primary'));
      button.classList.add('primary');
      const target = document.querySelector(button.dataset.tab);
      by('[data-panel]').forEach((panel) => panel.hidden = panel !== target);
    });
  });
}

function renderDatabase(database) {
  state.database = database;
  const reachable = Boolean(database?.reachable);
  const bar = one('[data-db-bar]');
  if (bar) {
    bar.style.width = reachable ? '100%' : '18%';
    bar.style.background = reachable ? 'var(--green)' : 'var(--red)';
  }
  const dbLabel = reachable ? `DB ${database.mode}` : 'DB indisponível';
  text('[data-db-label]', dbLabel);
  const mobileDb = one('[data-db-mobile]');
  if (mobileDb) {
    mobileDb.textContent = dbLabel;
    mobileDb.className = `pill db-mobile ${reachable ? 'ok' : 'danger'}`;
    mobileDb.hidden = false;
  }
  text('[data-db-mode]', database?.mode || '--');
  text('[data-db-url]', database?.url || 'URL indisponível');
  Object.entries(database?.tables || {}).forEach(([key, value]) => {
    text(`[data-table-count="${key}"]`, value);
  });
  const rows = Object.entries(database?.tables || {}).map(([name, value]) => `
    <tr><td data-label="Tabela">${esc(name)}</td><td data-label="Registos">${esc(value)}</td><td data-label="Estado"><span class="pill ${reachable ? 'ok' : 'danger'}">${reachable ? 'ok' : 'erro'}</span></td></tr>
  `).join('');
  html('[data-db-tables]', rows || emptyRow(3, 'Sem contagens de tabelas.'));
}

function renderOverview(overview) {
  state.overview = overview;
  state.allRuns = overview?.recent_runs || [];
  const summary = overview?.summary || {};
  text('[data-kpi="pipelines"]', summary.pipelines ?? 0);
  text('[data-kpi="runs"]', summary.runs ?? 0);
  text('[data-kpi="failed"]', summary.failed ?? 0);
  text('[data-kpi="success_rate"]', `${summary.success_rate ?? 0}%`);

  const pipelines = dedupePipelines(overview?.pipelines || []);
  state.pipelines = pipelines;
  text('[data-count="pipelines"]', `${pipelines.length} deployment(s) activo(s).`);
  html('[data-pipelines]', pipelines.length ? pipelines.map((item) => {
    const stale = deploymentShowsStale(item);
    const statusKlass = stale ? 'stale' : statusClass(item.last_status);
    const statusText = stale ? 'stale' : statusLabel(item.last_status);
    const label = pipelineLabel(item);
    return `
    <tr data-search-row data-state="${stateBucket(item.last_status)}" data-name="${esc(label.title)}" data-pipeline="${esc(item.pipeline_id)}" data-host="${esc(effectiveHostId(item))}" data-owner="${esc(item.owner)}" data-schedule="${esc(item.schedule)}" data-criticality="${esc(item.criticality)}" data-platform="${esc(item.runner_platform || '')}" data-state-label="${esc(statusText)}" data-last-run="${esc(item.last_run_id || '')}">
      <td data-label="Pipeline"><span class="name-cell"><span class="dot ${statusKlass}"></span><a href="${esc(lineageUrl(item.pipeline_id, item.host_id))}">${pipelineLabelHtml(label, effectiveHostId(item))}</a></span></td>
      <td data-label="Host">${esc(hostDisplay(item))}</td>
      <td data-label="Estado"><span class="pill ${statusKlass}">${esc(statusText)}</span></td>
      <td data-label="Dono">${esc(item.owner)}</td>
      <td data-label="Agenda"><span class="mono">${esc(item.schedule)}</span></td>
      <td data-label="Última run">${esc(formatDate(item.last_started_at))}</td>
      <td data-label="Duração">${esc(duration(item.last_duration_sec))}</td>
      <td data-label="Criticidade"><span class="pill ${criticalityClass(item.criticality)}">${esc(item.criticality)}</span></td>
    </tr>`;
  }).join('') : emptyRow(8, 'Ainda não há deployments. Verifica o catálogo YAML ou telemetria.'));

  bindHostFilters();
  applyPipelineFilters();

  if (pipelines[0] && !state.selectedPipeline) {
    setInspectorSelection(pipelines[0]);
  } else if (state.selectedPipeline) {
    const refreshed = findPipelineRow(state.selectedPipeline.pipeline_id, state.selectedPipeline.host_id);
    if (refreshed) setInspectorSelection(refreshed);
    else renderDeploymentRuns(state.selectedPipeline);
  }

  by('[data-pipelines] tr[data-name]').forEach((row) => {
    row.addEventListener('click', () => {
      by('[data-pipelines] tr').forEach((item) => item.classList.remove('is-selected'));
      row.classList.add('is-selected');
      const item = findPipelineRow(row.dataset.pipeline, row.dataset.host)
        || {
          pipeline_id: row.dataset.pipeline,
          host_id: row.dataset.host,
          name: row.dataset.name,
          owner: row.dataset.owner,
          schedule: row.dataset.schedule,
          criticality: row.dataset.criticality,
          runner_platform: row.dataset.platform,
          last_status: row.dataset.stateLabel,
          last_run_id: row.dataset.lastRun,
        };
      setInspectorSelection(item);
    });
  });
}

async function loadDashboard() {
  setSync('A carregar');
  setAlert();
  updateTokenBanner();
  try {
    const [overview, database] = await Promise.all([api('/v1/read/overview'), api('/v1/read/database')]);
    renderOverview(overview.data);
    renderDatabase(database.database);
    setSync('Sincronizado', 'ok');
    if (!database.database?.reachable) setAlert('Base de dados indisponível.', 'error');
  } catch (error) {
    setSync('Erro', 'danger');
    setAlert(error.message, 'error');
  }
}

function renderRunnerHosts(payload) {
  state.runnerHosts = payload;
  const rows = (payload?.hosts || []).map((host) => `
    <tr>
      <td data-label="Host">${esc(host.host_id)}</td>
      <td data-label="Plataforma">${esc(host.platform)}</td>
      <td data-label="SSH"><span class="mono">${esc(host.ssh || '—')}</span></td>
      <td data-label="Repo"><span class="mono">${esc(host.repo_path || '—')}</span></td>
    </tr>
  `).join('');
  html('[data-runner-hosts]', rows || emptyRow(4, 'Sem hosts em deploy/runners/hosts.yaml.'));
  const syncPill = one('[data-ssh-sync-flag]');
  if (syncPill) {
    const enabled = Boolean(payload?.ssh_sync_enabled);
    syncPill.className = `pill ${enabled ? 'ok' : 'warn'}`;
    syncPill.textContent = enabled ? 'SSH sync activo' : 'SSH sync desactivado';
  }
}

function taskSchedulerHostId(heartbeat, scheduler) {
  return scheduler?.host_id || heartbeat.host_id || heartbeat.hostname || heartbeat.source_id || '--';
}

function taskSchedulerIssueCount(scheduler) {
  if (!scheduler) return 0;
  const pipelineIssues = (scheduler.pipelines || []).filter((item) => (
    !item.task_found || (item.last_task_result !== null && item.last_task_result !== undefined && Number(item.last_task_result) !== 0)
  )).length;
  return pipelineIssues + (scheduler.ok === false ? 1 : 0);
}

function latestTaskSchedulerSnapshots(heartbeats) {
  const snapshots = new Map();
  (heartbeats || []).forEach((heartbeat) => {
    const scheduler = heartbeat.payload?.task_scheduler;
    if (!scheduler || typeof scheduler !== 'object') return;
    const hostId = taskSchedulerHostId(heartbeat, scheduler);
    const current = snapshots.get(hostId);
    const seenAt = new Date(scheduler.collected_at || heartbeat.seen_at || 0).getTime();
    const currentSeenAt = current ? new Date(current.scheduler.collected_at || current.heartbeat.seen_at || 0).getTime() : -1;
    if (!current || seenAt >= currentSeenAt) {
      snapshots.set(hostId, { hostId, heartbeat, scheduler });
    }
  });
  return [...snapshots.values()].sort((left, right) => String(left.hostId).localeCompare(String(right.hostId)));
}

function taskResultLabel(value) {
  if (value === null || value === undefined || value === '') return '--';
  const numeric = Number(value);
  if (Number.isFinite(numeric) && numeric === 0) return '0';
  return String(value);
}

function renderTaskSchedulerInventory(heartbeats) {
  const snapshots = latestTaskSchedulerSnapshots(heartbeats);
  const pipelineRows = snapshots.flatMap((snapshot) => (
    (snapshot.scheduler.pipelines || []).map((pipeline) => ({ ...pipeline, host_id: snapshot.hostId }))
  ));
  const issueCount = snapshots.reduce((total, snapshot) => total + taskSchedulerIssueCount(snapshot.scheduler), 0);
  const latestCollected = snapshots
    .map((snapshot) => snapshot.scheduler.collected_at || snapshot.heartbeat.seen_at)
    .filter(Boolean)
    .sort((left, right) => new Date(right) - new Date(left))[0];

  text('[data-task-scheduler-kpi="hosts"]', snapshots.length);
  text('[data-task-scheduler-kpi="tasks"]', pipelineRows.filter((item) => item.task_found).length);
  text('[data-task-scheduler-kpi="issues"]', issueCount);
  text('[data-task-scheduler-latest]', formatDate(latestCollected));

  html('[data-task-scheduler-hosts]', snapshots.length ? snapshots.map((snapshot) => {
    const scheduler = snapshot.scheduler;
    const pipelines = scheduler.pipelines || [];
    const issues = taskSchedulerIssueCount(scheduler);
    const ok = scheduler.ok !== false && issues === 0;
    return `
      <tr>
        <td data-label="Host">${esc(snapshot.hostId)}</td>
        <td data-label="Tasks">${esc(pipelines.filter((item) => item.task_found).length)} / ${esc(pipelines.length)}</td>
        <td data-label="Erros">${esc(issues)}</td>
        <td data-label="Recolha">${esc(formatDate(scheduler.collected_at || snapshot.heartbeat.seen_at))}</td>
        <td data-label="Estado"><span class="pill ${ok ? 'ok' : 'danger'}">${esc(ok ? 'ok' : (scheduler.error || 'atenção'))}</span></td>
      </tr>`;
  }).join('') : emptyRow(5, 'Sem inventário Task Scheduler nos heartbeats recentes.'));

  html('[data-task-scheduler-pipelines]', pipelineRows.length ? pipelineRows.map((pipeline) => {
    const result = taskResultLabel(pipeline.last_task_result);
    const resultOk = result === '--' || result === '0';
    const taskLabel = pipeline.task_found ? `${pipeline.task_path || ''}${pipeline.task_name || ''}` : (pipeline.expected_task_name || '--');
    const pipelineLabelData = pipelineLabel(null, pipeline.pipeline_id, pipeline.host_id);
    return `
      <tr>
        <td data-label="Pipeline">${pipelineLabelHtml(pipelineLabelData, pipeline.host_id)}</td>
        <td data-label="Task"><span class="mono">${esc(taskLabel)}</span></td>
        <td data-label="Estado"><span class="pill ${pipeline.task_found ? statusClass(pipeline.state) || 'ok' : 'danger'}">${esc(pipeline.task_found ? (pipeline.state || '--') : 'não encontrada')}</span></td>
        <td data-label="Próxima execução">${esc(formatDate(pipeline.next_run_time))}</td>
        <td data-label="Último resultado"><span class="pill ${resultOk ? 'ok' : 'danger'}">${esc(result)}</span></td>
      </tr>`;
  }).join('') : emptyRow(5, 'Sem pipelines Task Scheduler nos heartbeats recentes.'));
}

async function loadEnvironment() {
  setSync('A carregar');
  setAlert();
  updateTokenBanner();
  try {
    const [database, heartbeatsResponse, triggersResponse, hosts] = await Promise.all([
      api('/v1/read/database'),
      api('/v1/read/heartbeats?limit=50'),
      api('/v1/read/triggers?limit=50'),
      api('/v1/read/runner-hosts').catch(() => ({ hosts: [], ssh_sync_enabled: false })),
    ]);
    renderDatabase(database.database);
    renderRunnerHosts(hosts);
    const heartbeats = heartbeatsResponse.items || [];
    const triggers = triggersResponse.items || [];
    renderTaskSchedulerInventory(heartbeats);
    text('[data-count-kpi="heartbeats"]', heartbeats.length);
    text('[data-count-kpi="heartbeats_ok"]', heartbeats.filter((item) => item.status === 'ok').length);
    text('[data-last-heartbeat]', formatDate(heartbeats[0]?.seen_at));
    text('[data-count-kpi="triggers"]', triggers.length);
    text('[data-count-kpi="queued"]', triggers.filter((item) => item.status === 'queued').length);
    text('[data-count-kpi="claimed"]', triggers.filter((item) => item.status === 'claimed').length);
    text('[data-count-kpi="completed"]', triggers.filter((item) => ['ok', 'done', 'completed'].includes(String(item.status).toLowerCase())).length);
    const hostSet = new Set(heartbeats.map((item) => item.host_id || item.hostname || item.source_id).filter(Boolean));
    html('[data-activity]', [
      ...heartbeats.slice(0, 8).map((item) => {
        const label = pipelineLabel(null, item.pipeline_id, item.host_id);
        return `<div class="deploy-item">${pipelineLabelHtml(label, item.host_id || item.hostname || '')}<p class="mono">${esc(item.source_id || item.source_type || '--')} · ${esc(formatDate(item.seen_at))} · ${esc(item.status)}</p></div>`;
      }),
      ...triggers.slice(0, 5).map((item) => {
        const label = pipelineLabel(null, item.pipeline_id, item.host_id);
        return `<div class="deploy-item">${pipelineLabelHtml(label, item.host_id || '')}<p class="mono">${esc(item.trigger_id)} · ${esc(item.status)}</p></div>`;
      }),
    ].join('') || `<div class="deploy-item"><strong>Sem atividade</strong><p class="mono">Ainda não há heartbeats ou triggers.</p></div>`);
    text('[data-count-kpi="sources"]', hostSet.size);
    setSync('Sincronizado', 'ok');
  } catch (error) {
    setSync('Erro', 'danger');
    setAlert(error.message, 'error');
  }
}

function renderRunDetail(detail) {
  const run = detail?.run;
  const modules = detail?.modules || [];
  const logs = detail?.logs || [];
  const copy = one('[data-copy]');
  if (copy) copy.dataset.copy = run?.run_id || '';
  text('[data-current-run]', run?.run_id || 'sem run');
  const runLabel = run ? pipelineLabel(run) : null;
  text('[data-run-crumb]', run ? `Runs / ${runLabel.title} / ${run.status}` : 'Runs / sem dados');
  const titleEl = one('[data-run-title]');
  if (titleEl) {
    titleEl.innerHTML = run ? pipelineLabelHtml(runLabel, run.host_id || '') : 'Runs';
  }
  text('[data-run-summary]', run ? `${run.run_id} · ${run.status}` : 'Sem run selecionada.');
  const sync = one('[data-sync-state]');
  if (sync && run) {
    sync.className = `pill ${statusClass(run.status)}`;
    sync.textContent = run.status;
  }
  text('[data-run-started]', formatDate(run?.started_at));
  text('[data-run-duration]', duration(run?.duration_sec));
  text('[data-run-module-count]', modules.length);
  text('[data-run-log-count]', logs.length);
  text('[data-count="modules"]', `${modules.length} módulo(s).`);
  html('[data-run-modules]', modules.length ? modules.map((item) => `
    <tr data-state="${stateBucket(item.status)}">
      <td data-label="Módulo">${esc(item.module_id)}</td>
      <td data-label="Estado"><span class="pill ${statusClass(item.status)}">${esc(statusLabel(item.status))}</span></td>
      <td data-label="Início">${esc(formatDate(item.started_at))}</td>
      <td data-label="Duração">${esc(duration(item.duration_sec))}</td>
      <td data-label="Pipeline">${pipelineLabelHtml(pipelineLabel(null, item.pipeline_id), '')}</td>
      <td data-label="Erro">${esc(item.error_message || '--')}</td>
    </tr>
  `).join('') : emptyRow(6, 'Sem módulos registados para esta run.'));
  html('[data-run-logs]', logs.length ? logs.slice(0, 50).map((item) => `
    <div class="log-line" data-search-row><span>${esc(formatDate(item.created_at))}</span><span>${esc(item.level)}</span><span>${esc(item.message)}</span></div>
  `).join('') : `<div class="log-line" data-search-row><span>--</span><span>INFO</span><span>Sem logs registados.</span></div>`);
  bindSearch();
}

function renderRunsList(runs, selectedRunId) {
  html('[data-runs-list]', runs.length ? runs.map((run) => {
    const dep = findPipelineRow(run.pipeline_id, run.host_id);
    const stale = isStaleRun(run.started_at, run.status, deploymentStaleFlag(dep), dep?.schedule);
    const klass = stale ? 'stale' : statusClass(run.status);
    const selected = run.run_id === selectedRunId ? ' is-selected' : '';
    const label = pipelineLabel(run);
    return `
    <a class="run-list-item${selected}" href="${esc(runDetailUrl(run))}" data-search-row>
      <div class="run-list-main">
        ${pipelineLabelHtml(label, run.host_id || '')}
      </div>
      <div class="run-list-meta mono">
        <span>${esc(formatDate(run.started_at))}</span>
        <span class="pill ${klass}">${esc(stale ? 'stale' : statusLabel(run.status))}</span>
      </div>
    </a>`;
  }).join('') : emptyBlock('Sem runs registadas.'));
  text('[data-count="runs-list"]', `${runs.length} run(s) recente(s).`);
}

async function loadRuns() {
  setSync('A carregar');
  setAlert();
  try {
    const params = new URLSearchParams(window.location.search);
    const requestedRun = params.get('run') || '';
    const filterPipeline = params.get('pipeline') || '';
    const filterHost = params.get('host') || '';
    const runsQuery = new URLSearchParams({ limit: '80' });
    if (filterPipeline) runsQuery.set('pipeline_id', filterPipeline);
    if (filterHost) runsQuery.set('host_id', filterHost);

    const [runsResponse, pipelinesResponse, database] = await Promise.all([
      api(`/v1/read/runs?${runsQuery.toString()}`),
      api('/v1/read/pipelines'),
      api('/v1/read/database'),
    ]);
    state.pipelines = dedupePipelines(pipelinesResponse.items || []);
    renderDatabase(database.database);
    const runs = runsResponse.items || [];
    const run = runs.find((item) => item.run_id === requestedRun) || runs[0];
    renderRunsList(runs, run?.run_id);
    if (!run) {
      renderRunDetail(null);
      setSync('Sem runs', 'warn');
      return;
    }
    const detail = await api(`/v1/read/runs/${encodeURIComponent(run.run_id)}`);
    renderRunDetail(detail);
    setSync('Sincronizado', 'ok');
  } catch (error) {
    setSync('Erro', 'danger');
    setAlert(error.message, 'error');
  }
}

function latestStatusByModule(modules) {
  const latest = new Map();
  modules.forEach((item) => {
    if (!latest.has(item.module_id)) latest.set(item.module_id, item);
  });
  return latest;
}

function orderNodesLinear(nodes, edges) {
  if (!nodes.length) return [];
  const byId = new Map(nodes.map((node) => [node.module_id, node]));
  const targets = new Set(edges.map((edge) => edge.to_module_id));
  let current = nodes.find((node) => !targets.has(node.module_id))?.module_id || nodes[0].module_id;
  const ordered = [];
  const seen = new Set();
  while (current && !seen.has(current)) {
    seen.add(current);
    if (byId.has(current)) ordered.push(byId.get(current));
    current = edges.find((edge) => edge.from_module_id === current)?.to_module_id;
  }
  nodes.forEach((node) => {
    if (!seen.has(node.module_id)) ordered.push(node);
  });
  return ordered;
}

function computeBlockedDownstream(edges, latest) {
  const failed = new Set();
  latest.forEach((item, moduleId) => {
    if (statusClass(item.status) === 'danger') failed.add(moduleId);
  });
  const adj = new Map();
  edges.forEach((edge) => {
    if (!adj.has(edge.from_module_id)) adj.set(edge.from_module_id, []);
    adj.get(edge.from_module_id).push(edge.to_module_id);
  });
  const blocked = new Set();
  const queue = [...failed];
  while (queue.length) {
    const id = queue.shift();
    for (const next of adj.get(id) || []) {
      if (!blocked.has(next) && !failed.has(next)) {
        blocked.add(next);
        queue.push(next);
      }
    }
  }
  return blocked;
}

function renderNodeInspector(node, runtime, blocked) {
  const meta = node?.metadata || {};
  const command = Array.isArray(meta.command) ? meta.command.join(' ') : (meta.command || '--');
  html('[data-dag-inspector]', `
    <div class="kv"><span>Módulo</span><strong>${esc(node?.label || node?.module_id || '--')}</strong></div>
    <div class="kv"><span>Estado</span><strong>${esc(blocked ? 'blocked' : statusLabel(runtime?.status || 'sem runtime'))}</strong></div>
    <div class="kv"><span>Comando</span><strong class="mono">${esc(command)}</strong></div>
    <div class="kv"><span>Crítico</span><strong>${esc(meta.critical === false ? 'não' : 'sim')}</strong></div>
    ${runtime?.error_message ? `<div class="inspector-error">${esc(runtime.error_message)}</div>` : ''}
  `);
}

function renderDag(dag, modules, deployment = null, lastRun = null) {
  const pipeline = dag?.pipeline;
  const nodes = dag?.nodes || [];
  const edges = dag?.edges || [];
  const latest = latestStatusByModule(modules || []);
  const blocked = computeBlockedDownstream(edges, latest);
  const ordered = orderNodesLinear(nodes, edges);
  const hostLabel = deployment?.host_id || pipeline?.host_id || '--';
  text('[data-dag-title]', pipeline?.name || pipeline?.pipeline_id || 'Catálogo DAG');
  const dagLabel = pipeline ? pipelineLabel(pipeline) : null;
  text('[data-dag-crumb]', pipeline ? `DAG / ${dagLabel.title} @ ${hostLabel}` : 'DAG / sem catálogo');
  text('[data-dag-summary]', `${nodes.length} node(s), ${edges.length} dependência(s).${lastRun ? ` Última run: ${lastRun.run_id}.` : ''}`);
  text('[data-count="edges"]', `${edges.length} dependência(s).`);
  if (!state.selectedNodeId && ordered[0]) state.selectedNodeId = ordered[0].module_id;
  const selected = ordered.find((node) => node.module_id === state.selectedNodeId) || ordered[0];
  if (selected) {
    renderNodeInspector(selected, latest.get(selected.module_id), blocked.has(selected.module_id));
  } else {
    html('[data-dag-inspector]', pipeline ? `
      <div class="kv"><span>Pipeline</span><strong>${pipelineLabelHtml(pipelineLabel(pipeline), hostLabel)}</strong></div>
      <div class="kv"><span>Host</span><strong>${esc(hostLabel)}</strong></div>
      <div class="kv"><span>Dono</span><strong>${esc(pipeline.owner)}</strong></div>
      <div class="kv"><span>Agenda</span><strong>${esc(pipeline.schedule)}</strong></div>
    ` : `<div class="kv"><span>Pipeline</span><strong>--</strong></div>`);
  }

  const nodeHtml = ordered.length ? ordered.map((node, index) => {
    const left = 30 + index * 230;
    const top = 120;
    const runtime = latest.get(node.module_id);
    const isBlocked = blocked.has(node.module_id);
    const schedule = deployment?.schedule || pipeline?.schedule;
    const stale = isStaleRun(runtime?.started_at, runtime?.status, false, schedule);
    const klass = isBlocked ? 'blocked' : (stale ? 'stale' : statusClass(runtime?.status));
    const selectedClass = node.module_id === state.selectedNodeId ? ' is-selected' : '';
    return `<article class="node${selectedClass}" data-node-id="${esc(node.module_id)}" style="left:${left}px;top:${top}px"><span>${esc(node.type || 'task')}</span><strong>${esc(node.label || node.module_id)}</strong><p class="mono">${esc(node.module_id)}</p><span class="pill ${klass}">${esc(isBlocked ? 'blocked' : (stale ? 'stale' : statusLabel(runtime?.status || 'sem runtime')))}</span></article>`;
  }).join('') : `<article class="node" style="left:30px;top:110px"><span>empty</span><strong>Sem catálogo</strong><p>Regista um DAG em /v1/catalog/pipelines.</p><span class="pill warn">vazio</span></article>`;
  const edgeHtml = ordered.slice(0, -1).map((node, index) => {
    const left = 30 + index * 230 + 180;
    const nextBlocked = blocked.has(ordered[index + 1].module_id);
    return `<div class="edge ${nextBlocked ? 'blocked' : ''}" style="left:${left}px;top:168px;width:70px"></div>`;
  }).join('');
  html('[data-dag-board]', edgeHtml + nodeHtml);
  html('[data-dag-edges]', edges.length ? edges.map((edge) => `
    <div class="alert-item"><div><strong>${esc(edge.from_module_id)}</strong><p>${esc(edge.to_module_id)}</p></div><span class="pill">edge</span></div>
  `).join('') : emptyBlock('Sem dependências registadas.'));
  by('[data-dag-board] .node[data-node-id]').forEach((nodeEl) => {
    nodeEl.addEventListener('click', () => {
      state.selectedNodeId = nodeEl.dataset.nodeId;
      const node = ordered.find((item) => item.module_id === state.selectedNodeId);
      renderNodeInspector(node, latest.get(state.selectedNodeId), blocked.has(state.selectedNodeId));
      by('[data-dag-board] .node').forEach((item) => item.classList.toggle('is-selected', item === nodeEl));
    });
  });
}

async function loadLineage() {
  setSync('A carregar');
  setAlert();
  try {
    const params = new URLSearchParams(window.location.search);
    const urlPipeline = params.get('pipeline');
    const urlHost = params.get('host') || '';
    if (urlPipeline) state.selectedDeploymentKey = `${urlPipeline}::${urlHost}`;

    const pipelinesResponse = await api('/v1/read/pipelines');
    state.pipelines = dedupePipelines(pipelinesResponse.items || []);
    const select = one('[data-pipeline-select]');
    if (select) {
      if (!state.selectedDeploymentKey && state.pipelines[0]) {
        state.selectedDeploymentKey = deploymentKey(state.pipelines[0]);
      }
      select.innerHTML = state.pipelines.length
        ? state.pipelines.map((item) => `<option value="${esc(deploymentKey(item))}">${esc(pipelineDisplayName(item))} @ ${esc(hostDisplay(item))}</option>`).join('')
        : '<option value="">Sem pipelines</option>';
      select.value = state.selectedDeploymentKey;
      select.onchange = () => {
        state.selectedDeploymentKey = select.value;
        state.selectedNodeId = '';
        sessionStorage.setItem('overseer_selected_deployment', state.selectedDeploymentKey);
        const { pipelineId, hostId } = parseDeploymentKey(state.selectedDeploymentKey);
        const next = new URL(window.location.href);
        next.searchParams.set('pipeline', pipelineId);
        if (hostId) next.searchParams.set('host', hostId);
        else next.searchParams.delete('host');
        window.history.replaceState({}, '', next);
        loadLineage();
      };
    }
    const { pipelineId, hostId } = parseDeploymentKey(state.selectedDeploymentKey);
    if (!pipelineId) {
      renderDag(null, []);
      setSync('Sem catálogo', 'warn');
      return;
    }
    const deployment = state.pipelines.find((item) => item.pipeline_id === pipelineId && (item.host_id || '') === hostId);
    const runsUrl = `/v1/read/runs?pipeline_id=${encodeURIComponent(pipelineId)}&host_id=${encodeURIComponent(hostId)}&limit=1`;
    const dagUrl = `/v1/read/pipelines/${encodeURIComponent(pipelineId)}/dag?host_id=${encodeURIComponent(hostId)}`;
    const [dagResponse, runsResponse] = await Promise.all([
      api(dagUrl),
      api(runsUrl),
    ]);
    const lastRun = runsResponse.items?.[0];
    let modules = [];
    if (lastRun?.run_id) {
      const detail = await api(`/v1/read/runs/${encodeURIComponent(lastRun.run_id)}`);
      modules = detail.modules || [];
    }
    renderDag(dagResponse.dag, modules, deployment, lastRun);
    setSync('Sincronizado', 'ok');
  } catch (error) {
    setSync('Erro', 'danger');
    setAlert(error.message, 'error');
  }
}

function init() {
  const view = document.body.dataset.view || 'dashboard';
  renderAppNav(view);
  const loaders = {
    dashboard: loadDashboard,
    runs: loadRuns,
    lineage: loadLineage,
    deployments: loadEnvironment,
  };
  const load = loaders[view] || loadDashboard;
  bindChrome(load);
  bindFilters();
  bindSearch();
  bindCopy();
  bindTabs();
  bindKpiActions();
  load();
}

init();
