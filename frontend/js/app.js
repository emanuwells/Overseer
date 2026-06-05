const by = (selector, root = document) => Array.from(root.querySelectorAll(selector));
const one = (selector, root = document) => root.querySelector(selector);

const state = {
  overview: null,
  database: null,
  pipelines: [],
  selectedPipelineId: sessionStorage.getItem('overseer_selected_pipeline') || '',
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

function emptyRow(columns, label) {
  return `<tr><td colspan="${columns}"><span class="empty-state">${esc(label)}</span></td></tr>`;
}

function emptyBlock(label) {
  return `<div class="empty-state">${esc(label)}</div>`;
}

function bindChrome(refreshFn) {
  const input = one('[data-token-input]');
  if (input) input.value = apiToken();
  one('[data-token-save]')?.addEventListener('click', () => {
    const value = input?.value.trim() || '';
    if (value) sessionStorage.setItem('overseer_api_token', value);
    else sessionStorage.removeItem('overseer_api_token');
    refreshFn();
  });
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

  const pipelines = overview?.pipelines || [];
  state.pipelines = pipelines;
  text('[data-count="pipelines"]', `${pipelines.length} pipeline(s) registado(s).`);
  html('[data-pipelines]', pipelines.length ? pipelines.map((item) => `
    <tr data-state="${stateBucket(item.last_status)}" data-name="${esc(item.pipeline_id)}" data-owner="${esc(item.owner)}" data-state-label="${esc(statusLabel(item.last_status))}" data-last-run="${esc(item.last_run_id || '')}">
      <td><span class="name-cell"><span class="dot ${statusClass(item.last_status)}"></span>${esc(item.pipeline_id)}</span></td>
      <td><span class="pill ${statusClass(item.last_status)}">${esc(statusLabel(item.last_status))}</span></td>
      <td>${esc(item.owner)}</td>
      <td>${esc(item.schedule)}</td>
      <td>${esc(formatDate(item.last_started_at))}</td>
      <td>${esc(duration(item.last_duration_sec))}</td>
      <td>${esc(item.criticality)}</td>
    </tr>
  `).join('') : emptyRow(7, 'Ainda não há pipelines registados por API.'));

  const runs = overview?.recent_runs || [];
  const inspector = one('#inspector');
  if (inspector && pipelines[0]) {
    text('[data-inspector-title]', pipelines[0].pipeline_id, inspector);
    text('[data-inspector-state]', statusLabel(pipelines[0].last_status), inspector);
    const copy = one('[data-copy]', inspector);
    if (copy) copy.dataset.copy = pipelines[0].last_run_id || '';
  }
  html('[data-recent-runs]', runs.length ? runs.slice(0, 8).map((run) => `
    <div class="alert-item"><div><strong>${esc(run.pipeline_id)}</strong><p>${esc(run.run_id)} · ${esc(formatDate(run.started_at))}</p></div><span class="pill ${statusClass(run.status)}">${esc(statusLabel(run.status))}</span></div>
  `).join('') : emptyBlock('Ainda não há runs recebidas.'));

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

function renderDag(dag, modules) {
  const pipeline = dag?.pipeline;
  const nodes = dag?.nodes || [];
  const edges = dag?.edges || [];
  const latest = latestStatusByModule(modules || []);
  text('[data-dag-title]', pipeline?.name || pipeline?.pipeline_id || 'Catálogo DAG');
  text('[data-dag-crumb]', pipeline ? `DAG / ${pipeline.pipeline_id}` : 'DAG / sem catálogo');
  text('[data-dag-summary]', `${nodes.length} node(s), ${edges.length} dependência(s).`);
  text('[data-count="edges"]', `${edges.length} dependência(s).`);
  html('[data-dag-inspector]', pipeline ? `
    <div class="kv"><span>Pipeline</span><strong>${esc(pipeline.pipeline_id)}</strong></div>
    <div class="kv"><span>Dono</span><strong>${esc(pipeline.owner)}</strong></div>
    <div class="kv"><span>Agenda</span><strong>${esc(pipeline.schedule)}</strong></div>
    <div class="kv"><span>Criticidade</span><strong>${esc(pipeline.criticality)}</strong></div>
  ` : `<div class="kv"><span>Pipeline</span><strong>--</strong></div>`);

  const positions = [
    [30, 110], [300, 135], [560, 205], [820, 165], [820, 315], [300, 330], [560, 390],
  ];
  const nodeHtml = nodes.length ? nodes.map((node, index) => {
    const [left, top] = positions[index % positions.length];
    const runtime = latest.get(node.module_id);
    return `<article class="node" style="left:${left}px;top:${top}px"><span>${esc(node.type || 'task')}</span><strong>${esc(node.label || node.module_id)}</strong><p>${esc(node.module_id)}</p><span class="pill ${statusClass(runtime?.status)}">${esc(statusLabel(runtime?.status || 'sem runtime'))}</span></article>`;
  }).join('') : `<article class="node" style="left:30px;top:110px"><span>empty</span><strong>Sem catálogo</strong><p>Regista um DAG em /v1/catalog/pipelines.</p><span class="pill warn">vazio</span></article>`;
  const edgeHtml = edges.slice(0, 6).map((_, index) => {
    const styles = [
      'left:170px;top:160px;width:180px;transform:rotate(8deg)',
      'left:390px;top:184px;width:190px;transform:rotate(17deg)',
      'left:610px;top:250px;width:190px;transform:rotate(-10deg)',
      'left:170px;top:360px;width:180px;transform:rotate(-8deg)',
      'left:390px;top:382px;width:190px;transform:rotate(-17deg)',
      'left:610px;top:340px;width:190px;transform:rotate(10deg)',
    ];
    return `<div class="edge" style="${styles[index]}"></div>`;
  }).join('');
  html('[data-dag-board]', edgeHtml + nodeHtml);
  html('[data-dag-edges]', edges.length ? edges.map((edge) => `
    <div class="alert-item"><div><strong>${esc(edge.from_module_id)}</strong><p>${esc(edge.to_module_id)}</p></div><span class="pill">edge</span></div>
  `).join('') : emptyBlock('Sem dependências registadas.'));
}

async function loadLineage() {
  setSync('A carregar');
  setAlert();
  try {
    const pipelinesResponse = await api('/v1/read/pipelines');
    state.pipelines = pipelinesResponse.items || [];
    const select = one('[data-pipeline-select]');
    if (select) {
      if (!state.selectedPipelineId && state.pipelines[0]) state.selectedPipelineId = state.pipelines[0].pipeline_id;
      select.innerHTML = state.pipelines.length ? state.pipelines.map((item) => `<option value="${esc(item.pipeline_id)}">${esc(item.pipeline_id)}</option>`).join('') : '<option value="">Sem pipelines</option>';
      select.value = state.selectedPipelineId;
      select.onchange = () => {
        state.selectedPipelineId = select.value;
        sessionStorage.setItem('overseer_selected_pipeline', state.selectedPipelineId);
        loadLineage();
      };
    }
    if (!state.selectedPipelineId) {
      renderDag(null, []);
      setSync('Sem catálogo', 'warn');
      return;
    }
    const [dagResponse, modulesResponse] = await Promise.all([
      api(`/v1/read/pipelines/${encodeURIComponent(state.selectedPipelineId)}/dag`),
      api(`/v1/read/modules?pipeline_id=${encodeURIComponent(state.selectedPipelineId)}`),
    ]);
    renderDag(dagResponse.dag, modulesResponse.items || []);
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
    const sources = new Set(heartbeats.map((item) => item.source_id));
    text('[data-count-kpi="heartbeats"]', heartbeats.length);
    text('[data-count-kpi="heartbeats_ok"]', heartbeats.filter((item) => item.status === 'ok').length);
    text('[data-last-heartbeat]', formatDate(heartbeats[0]?.seen_at));
    text('[data-count-kpi="sources"]', sources.size);
    text('[data-count-kpi="triggers"]', triggers.length);
    text('[data-count-kpi="queued"]', triggers.filter((item) => item.status === 'queued').length);
    text('[data-count-kpi="claimed"]', triggers.filter((item) => item.status === 'claimed').length);
    text('[data-count-kpi="completed"]', triggers.filter((item) => ['ok', 'done', 'completed'].includes(String(item.status).toLowerCase())).length);
    html('[data-activity]', [
      ...heartbeats.slice(0, 5).map((item) => `<div class="deploy-item"><strong>${esc(item.source_id)}</strong><p class="mono">${esc(item.pipeline_id || item.source_type)} · ${esc(formatDate(item.seen_at))} · ${esc(item.status)}</p></div>`),
      ...triggers.slice(0, 5).map((item) => `<div class="deploy-item"><strong>${esc(item.pipeline_id)}</strong><p class="mono">${esc(item.trigger_id)} · ${esc(item.status)}</p></div>`),
    ].join('') || `<div class="deploy-item"><strong>Sem atividade</strong><p class="mono">Ainda não há heartbeats ou triggers.</p></div>`);
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
