const by = (selector, root = document) => Array.from(root.querySelectorAll(selector));
const one = (selector, root = document) => root.querySelector(selector);

const state = {
  overview: null,
  database: null,
  pipelines: [],
  selectedDeploymentKey: sessionStorage.getItem('overseer_selected_deployment') || '',
  selectedNodeId: '',
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
  if (['ok', 'success', 'done', 'completed'].includes(raw)) return 'ok';
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

function pipelineRecencyScore(item) {
  const started = item?.last_started_at ? new Date(item.last_started_at).getTime() : 0;
  const cleanId = logicalPipelineId(item?.pipeline_id) === item?.pipeline_id ? 1 : 0;
  const hasHost = item?.host_id ? 1 : 0;
  return [Number.isFinite(started) ? started : 0, cleanId, hasHost];
}

function dedupePipelines(pipelines) {
  const best = new Map();
  (pipelines || []).forEach((item) => {
    const logicalId = logicalPipelineId(item.pipeline_id);
    if (!logicalId) return;
    const candidate = { ...item, pipeline_id: logicalId };
    const legacyHost = logicalPipelineId(item.pipeline_id) !== item.pipeline_id
      ? String(item.pipeline_id).split('__').pop()
      : '';
    if (legacyHost && !candidate.host_id) candidate.host_id = legacyHost;
    const prev = best.get(logicalId);
    if (!prev) {
      best.set(logicalId, candidate);
      return;
    }
    const a = pipelineRecencyScore(candidate);
    const b = pipelineRecencyScore(prev);
    if (a[0] > b[0] || (a[0] === b[0] && (a[1] > b[1] || (a[1] === b[1] && a[2] > b[2])))) {
      best.set(logicalId, candidate);
    }
  });
  return Array.from(best.values()).sort((left, right) => String(left.pipeline_id).localeCompare(String(right.pipeline_id)));
}

function deploymentKey(item) {
  return `${logicalPipelineId(item.pipeline_id)}::${item.host_id || ''}`;
}

function parseDeploymentKey(key) {
  const [pipelineId, hostId = ''] = String(key || '').split('::');
  return { pipelineId, hostId };
}

function pipelineDisplayName(item) {
  return item?.name || item?.pipeline_id || '--';
}

function hostDisplay(item) {
  return item?.host_id || item?.runner_host || '--';
}

function isStaleRun(startedAt, status) {
  if (String(status || '').toLowerCase() !== 'running' || !startedAt) return false;
  const date = new Date(startedAt);
  if (Number.isNaN(date.getTime())) return false;
  return Date.now() - date.getTime() > 24 * 60 * 60 * 1000;
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
  text('[data-db-label]', reachable ? `DB ${database.mode}` : 'DB indisponível');
  text('[data-db-mode]', database?.mode || '--');
  text('[data-db-url]', database?.url || 'URL indisponível');
  Object.entries(database?.tables || {}).forEach(([key, value]) => {
    text(`[data-table-count="${key}"]`, value);
  });
  const rows = Object.entries(database?.tables || {}).map(([name, value]) => `
    <tr><td>${esc(name)}</td><td>${esc(value)}</td><td><span class="pill ${reachable ? 'ok' : 'danger'}">${reachable ? 'ok' : 'erro'}</span></td></tr>
  `).join('');
  html('[data-db-tables]', rows || emptyRow(3, 'Sem contagens de tabelas.'));
}

function renderOverview(overview) {
  state.overview = overview;
  const summary = overview?.summary || {};
  text('[data-kpi="pipelines"]', summary.pipelines ?? 0);
  text('[data-kpi="runs"]', summary.runs ?? 0);
  text('[data-kpi="failed"]', summary.failed ?? 0);
  text('[data-kpi="success_rate"]', `${summary.success_rate ?? 0}%`);

  const pipelines = dedupePipelines(overview?.pipelines || []);
  state.pipelines = pipelines;
  text('[data-count="pipelines"]', `${pipelines.length} pipeline(s) registado(s).`);
  html('[data-pipelines]', pipelines.length ? pipelines.map((item) => {
    const stale = isStaleRun(item.last_started_at, item.last_status);
    const statusKlass = stale ? 'stale' : statusClass(item.last_status);
  const statusText = stale ? 'stale' : statusLabel(item.last_status);
    return `
    <tr data-state="${stateBucket(item.last_status)}" data-name="${esc(pipelineDisplayName(item))}" data-pipeline="${esc(item.pipeline_id)}" data-host="${esc(item.host_id || '')}" data-owner="${esc(item.owner)}" data-state-label="${esc(statusText)}" data-last-run="${esc(item.last_run_id || '')}">
      <td><span class="name-cell"><span class="dot ${statusKlass}"></span><a href="${esc(lineageUrl(item.pipeline_id, item.host_id))}">${esc(pipelineDisplayName(item))}</a></span></td>
      <td>${esc(hostDisplay(item))}</td>
      <td><span class="pill ${statusKlass}">${esc(statusText)}</span></td>
      <td>${esc(item.owner)}</td>
      <td>${esc(item.schedule)}</td>
      <td>${esc(formatDate(item.last_started_at))}</td>
      <td>${esc(duration(item.last_duration_sec))}</td>
      <td>${esc(item.criticality)}</td>
    </tr>`;
  }).join('') : emptyRow(8, 'Ainda não há pipelines registados por API.'));

  const runs = overview?.recent_runs || [];
  const inspector = one('#inspector');
  if (inspector && pipelines[0]) {
    text('[data-inspector-title]', `${pipelineDisplayName(pipelines[0])} · ${hostDisplay(pipelines[0])}`, inspector);
    text('[data-inspector-state]', statusLabel(pipelines[0].last_status), inspector);
    const copy = one('[data-copy]', inspector);
    if (copy) copy.dataset.copy = pipelines[0].last_run_id || '';
  }
  const recentByPipeline = new Map();
  runs.forEach((run) => {
    const key = logicalPipelineId(run.pipeline_id);
    const prev = recentByPipeline.get(key);
    if (!prev || new Date(run.started_at) > new Date(prev.started_at)) recentByPipeline.set(key, run);
  });
  const recentRuns = Array.from(recentByPipeline.values())
    .sort((a, b) => new Date(b.started_at) - new Date(a.started_at))
    .slice(0, 8);
  html('[data-recent-runs]', recentRuns.length ? recentRuns.map((run) => {
    const stale = isStaleRun(run.started_at, run.status);
    const klass = stale ? 'stale' : statusClass(run.status);
    return `
    <div class="alert-item"><div><strong>${esc(run.pipeline_id)}</strong><p>${esc(run.host_id || '--')} · ${esc(run.run_id)} · ${esc(formatDate(run.started_at))}</p></div><span class="pill ${klass}">${esc(stale ? 'stale' : statusLabel(run.status))}</span></div>`;
  }).join('') : emptyBlock('Ainda não há runs recebidas.'));

  by('[data-pipelines] tr[data-name]').forEach((row) => {
    row.addEventListener('click', () => {
      by('[data-pipelines] tr').forEach((item) => item.classList.remove('is-selected'));
      row.classList.add('is-selected');
      text('[data-inspector-title]', row.dataset.name);
      text('[data-inspector-state]', row.dataset.stateLabel);
      const copy = one('#inspector [data-copy]');
      if (copy) copy.dataset.copy = row.dataset.lastRun || '';
    });
  });
}

async function loadDashboard() {
  setSync('A carregar');
  setAlert();
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

function renderRunDetail(detail) {
  const run = detail?.run;
  const modules = detail?.modules || [];
  const logs = detail?.logs || [];
  const copy = one('[data-copy]');
  if (copy) copy.dataset.copy = run?.run_id || '';
  text('[data-current-run]', run?.run_id || 'sem run');
  text('[data-run-crumb]', run ? `Runs / ${run.pipeline_id} / ${run.status}` : 'Runs / sem dados');
  text('[data-run-title]', run?.pipeline_id || 'Runs');
  text('[data-run-summary]', run ? `${run.run_id} terminou com estado ${run.status}.` : 'Sem run selecionada.');
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
      <td>${esc(item.module_id)}</td>
      <td><span class="pill ${statusClass(item.status)}">${esc(statusLabel(item.status))}</span></td>
      <td>${esc(formatDate(item.started_at))}</td>
      <td>${esc(duration(item.duration_sec))}</td>
      <td>${esc(item.pipeline_id)}</td>
      <td>${esc(item.error_message || '--')}</td>
    </tr>
  `).join('') : emptyRow(6, 'Sem módulos registados para esta run.'));
  html('[data-run-logs]', logs.length ? logs.slice(0, 50).map((item) => `
    <div class="log-line" data-search-row><span>${esc(formatDate(item.created_at))}</span><span>${esc(item.level)}</span><span>${esc(item.message)}</span></div>
  `).join('') : `<div class="log-line" data-search-row><span>--</span><span>INFO</span><span>Sem logs registados.</span></div>`);
  bindSearch();
}

async function loadRuns() {
  setSync('A carregar');
  setAlert();
  try {
    const [runsResponse, database] = await Promise.all([api('/v1/read/runs?limit=1'), api('/v1/read/database')]);
    renderDatabase(database.database);
    const run = runsResponse.items?.[0];
    if (!run) {
      renderRunDetail(null);
      setSync('Sem runs', 'warn');
      return;
    }
    const detail = await api(`/v1/read/runs/${encodeURIComponent(run.run_id)}`);
    renderRunDetail(detail);
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
  text('[data-dag-crumb]', pipeline ? `DAG / ${pipeline.pipeline_id} @ ${hostLabel}` : 'DAG / sem catálogo');
  text('[data-dag-summary]', `${nodes.length} node(s), ${edges.length} dependência(s).${lastRun ? ` Última run: ${lastRun.run_id}.` : ''}`);
  text('[data-count="edges"]', `${edges.length} dependência(s).`);
  if (!state.selectedNodeId && ordered[0]) state.selectedNodeId = ordered[0].module_id;
  const selected = ordered.find((node) => node.module_id === state.selectedNodeId) || ordered[0];
  if (selected) {
    renderNodeInspector(selected, latest.get(selected.module_id), blocked.has(selected.module_id));
  } else {
    html('[data-dag-inspector]', pipeline ? `
      <div class="kv"><span>Pipeline</span><strong>${esc(pipeline.pipeline_id)}</strong></div>
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
    const stale = isStaleRun(runtime?.started_at, runtime?.status);
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
    const [dagResponse, runsResponse] = await Promise.all([
      api(`/v1/read/pipelines/${encodeURIComponent(pipelineId)}/dag`),
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

async function loadDeployments() {
  setSync('A carregar');
  setAlert();
  try {
    const [database, heartbeatsResponse, triggersResponse] = await Promise.all([
      api('/v1/read/database'),
      api('/v1/read/heartbeats?limit=50'),
      api('/v1/read/triggers?limit=50'),
    ]);
    renderDatabase(database.database);
    const heartbeats = heartbeatsResponse.items || [];
    const triggers = triggersResponse.items || [];
    text('[data-count-kpi="heartbeats"]', heartbeats.length);
    text('[data-count-kpi="heartbeats_ok"]', heartbeats.filter((item) => item.status === 'ok').length);
    text('[data-last-heartbeat]', formatDate(heartbeats[0]?.seen_at));
    text('[data-count-kpi="triggers"]', triggers.length);
    text('[data-count-kpi="queued"]', triggers.filter((item) => item.status === 'queued').length);
    text('[data-count-kpi="claimed"]', triggers.filter((item) => item.status === 'claimed').length);
    text('[data-count-kpi="completed"]', triggers.filter((item) => ['ok', 'done', 'completed'].includes(String(item.status).toLowerCase())).length);
    const hosts = new Set(heartbeats.map((item) => item.host_id || item.hostname || item.source_id).filter(Boolean));
    html('[data-activity]', [
      ...heartbeats.slice(0, 8).map((item) => `<div class="deploy-item"><strong>${esc(item.source_id)}</strong><p class="mono">${esc(item.host_id || item.hostname || '--')} · ${esc(item.pipeline_id || item.source_type)} · ${esc(formatDate(item.seen_at))} · ${esc(item.status)}</p></div>`),
      ...triggers.slice(0, 5).map((item) => `<div class="deploy-item"><strong>${esc(item.pipeline_id)}</strong><p class="mono">${esc(item.host_id || '--')} · ${esc(item.trigger_id)} · ${esc(item.status)}</p></div>`),
    ].join('') || `<div class="deploy-item"><strong>Sem atividade</strong><p class="mono">Ainda não há heartbeats ou triggers.</p></div>`);
    text('[data-count-kpi="sources"]', hosts.size);
    setSync('Sincronizado', 'ok');
  } catch (error) {
    setSync('Erro', 'danger');
    setAlert(error.message, 'error');
  }
}

function init() {
  const loaders = {
    dashboard: loadDashboard,
    runs: loadRuns,
    lineage: loadLineage,
    deployments: loadDeployments,
  };
  const load = loaders[document.body.dataset.view] || loadDashboard;
  bindChrome(load);
  bindFilters();
  bindSearch();
  bindCopy();
  bindTabs();
  load();
}

init();
