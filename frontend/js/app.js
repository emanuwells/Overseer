const state = {
  overview: null,
  database: null,
  pipelines: [],
  selectedPipelineId: sessionStorage.getItem('overseer_selected_pipeline') || '',
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));
}

function token() {
  return sessionStorage.getItem('overseer_api_token') || '';
}

async function api(path) {
  const headers = { Accept: 'application/json' };
  if (token()) headers.Authorization = `Bearer ${token()}`;
  const response = await fetch(path, { headers });
  if (response.status === 401) {
    throw new Error('API devolveu 401. Confirma o token configurado.');
  }
  if (!response.ok) {
    throw new Error(`API devolveu HTTP ${response.status}.`);
  }
  return response.json();
}

function setText(selector, value, root = document) {
  const target = $(selector, root);
  if (target) target.textContent = value;
}

function setAlert(message = '', type = '') {
  const target = $('[data-alert]');
  if (!target) return;
  target.innerHTML = message ? `<div class="alert ${esc(type)}">${esc(message)}</div>` : '';
}

function setSync(label, kind = '') {
  const target = $('[data-sync-state]');
  if (!target) return;
  target.className = `pill ${kind}`.trim();
  target.textContent = label;
}

function statusClass(status) {
  const raw = String(status || '').toLowerCase();
  if (['ok', 'success', 'done', 'completed'].includes(raw)) return 'ok';
  if (['warning', 'warn', 'queued', 'running', 'claimed'].includes(raw)) return 'warn';
  if (!raw) return '';
  return 'danger';
}

function statusLabel(status) {
  return status || 'sem estado';
}

function formatDate(value) {
  if (!value) return '--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('pt-PT');
}

function duration(value) {
  if (value === null || value === undefined || value === '') return '--';
  const seconds = Number(value);
  if (!Number.isFinite(seconds)) return String(value);
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

function emptyRow(columns, label) {
  return `<tr><td colspan="${columns}"><div class="empty">${esc(label)}</div></td></tr>`;
}

function emptyBlock(label) {
  return `<div class="empty">${esc(label)}</div>`;
}

function bindChrome(refreshFn) {
  const input = $('[data-token-input]');
  if (input) input.value = token();
  $('[data-token-save]')?.addEventListener('click', () => {
    const value = input?.value.trim() || '';
    if (value) sessionStorage.setItem('overseer_api_token', value);
    else sessionStorage.removeItem('overseer_api_token');
    refreshFn();
  });
  $('[data-refresh]')?.addEventListener('click', refreshFn);
}

function renderDatabase(database) {
  state.database = database;
  const reachable = Boolean(database?.reachable);
  const bar = $('[data-db-bar]');
  if (bar) {
    bar.style.width = reachable ? '100%' : '18%';
    bar.style.background = reachable ? 'var(--green)' : 'var(--red)';
  }
  setText('[data-db-mode]', database?.mode || '--');
  setText('[data-db-driver]', database?.driver || '--');
  Object.entries(database?.tables || {}).forEach(([key, value]) => {
    setText(`[data-table-count="${key}"]`, value);
  });
}

function renderOverview(overview) {
  state.overview = overview;
  const summary = overview?.summary || {};
  setText('[data-kpi="pipelines"]', summary.pipelines ?? 0);
  setText('[data-kpi="runs"]', summary.runs ?? 0);
  setText('[data-kpi="running"]', summary.running ?? 0);
  setText('[data-kpi="success_rate"]', `${summary.success_rate ?? 0}%`);

  const pipelines = overview?.pipelines || [];
  state.pipelines = pipelines;
  setText('[data-count="pipelines"]', `${pipelines.length} pipeline(s)`);
  const pipelineBody = $('[data-pipelines]');
  if (pipelineBody) {
    pipelineBody.innerHTML = pipelines.length ? pipelines.map((item) => `
      <tr>
        <td><span class="name-cell"><span class="dot ${statusClass(item.last_status)}"></span>${esc(item.pipeline_id)}</span></td>
        <td><span class="pill ${statusClass(item.last_status)}">${esc(statusLabel(item.last_status))}</span></td>
        <td>${esc(item.owner)}</td>
        <td>${esc(item.schedule)}</td>
        <td>${esc(formatDate(item.last_started_at))}</td>
      </tr>
    `).join('') : emptyRow(5, 'Ainda não há pipelines registados por API.');
  }

  const runs = overview?.recent_runs || [];
  setText('[data-count="runs"]', `${runs.length} run(s)`);
  const recent = $('[data-recent-runs]');
  if (recent) {
    recent.innerHTML = runs.length ? runs.slice(0, 8).map((run) => `
      <div class="alert-item">
        <div><strong>${esc(run.pipeline_id)}</strong><p>${esc(run.run_id)} · ${esc(formatDate(run.started_at))}</p></div>
        <span class="pill ${statusClass(run.status)}">${esc(statusLabel(run.status))}</span>
      </div>
    `).join('') : emptyBlock('Ainda não há runs recebidas.');
  }
}

async function loadDashboard() {
  setSync('A carregar');
  setAlert();
  try {
    const [overviewResponse, databaseResponse] = await Promise.all([
      api('/v1/read/overview'),
      api('/v1/read/database'),
    ]);
    renderOverview(overviewResponse.data);
    renderDatabase(databaseResponse.database);
    setSync('Sincronizado', 'ok');
    if (!databaseResponse.database?.reachable) setAlert('Base de dados indisponível.', 'error');
  } catch (error) {
    setSync('Erro', 'danger');
    setAlert(error.message, 'error');
  }
}

function renderRunDetail(detail) {
  const run = detail?.run;
  setText('[data-run-title]', run ? run.run_id : 'Detalhe');
  setText('[data-run-subtitle]', run ? run.pipeline_id : 'Sem run selecionada');
  const box = $('[data-run-detail]');
  if (box) {
    box.innerHTML = run ? `
      <div class="kv"><span>Estado</span><strong>${esc(run.status)}</strong></div>
      <div class="kv"><span>Início</span><strong>${esc(formatDate(run.started_at))}</strong></div>
      <div class="kv"><span>Fim</span><strong>${esc(formatDate(run.ended_at))}</strong></div>
      <div class="kv"><span>Duração</span><strong>${esc(duration(run.duration_sec))}</strong></div>
    ` : emptyBlock('Sem detalhe disponível.');
  }

  const modules = detail?.modules || [];
  const moduleBox = $('[data-run-modules]');
  if (moduleBox) {
    moduleBox.innerHTML = modules.length ? modules.map((item) => `
      <div class="alert-item">
        <div><strong>${esc(item.module_id)}</strong><p>${esc(item.error_message || formatDate(item.started_at))}</p></div>
        <span class="pill ${statusClass(item.status)}">${esc(statusLabel(item.status))}</span>
      </div>
    `).join('') : emptyBlock('Sem módulos registados para esta run.');
  }

  const logs = detail?.logs || [];
  const logBox = $('[data-run-logs]');
  if (logBox) {
    logBox.innerHTML = logs.length ? logs.slice(0, 20).map((item) => `
      <div class="log-entry"><strong>${esc(item.level)}</strong> ${esc(formatDate(item.created_at))}<br>${esc(item.message)}</div>
    `).join('') : emptyBlock('Sem logs registados para esta run.');
  }
}

async function selectRun(runId) {
  if (!runId) {
    renderRunDetail(null);
    return;
  }
  const detail = await api(`/v1/read/runs/${encodeURIComponent(runId)}`);
  renderRunDetail(detail);
}

async function loadRuns() {
  setSync('A carregar');
  setAlert();
  try {
    const [runsResponse, databaseResponse] = await Promise.all([
      api('/v1/read/runs?limit=100'),
      api('/v1/read/database'),
    ]);
    renderDatabase(databaseResponse.database);
    const runs = runsResponse.items || [];
    setText('[data-count="runs"]', `${runs.length} run(s)`);
    const body = $('[data-runs]');
    if (body) {
      body.innerHTML = runs.length ? runs.map((run, index) => `
        <tr data-run-id="${esc(run.run_id)}" class="${index === 0 ? 'is-selected' : ''}">
          <td>${esc(run.run_id)}</td>
          <td>${esc(run.pipeline_id)}</td>
          <td><span class="pill ${statusClass(run.status)}">${esc(statusLabel(run.status))}</span></td>
          <td>${esc(formatDate(run.started_at))}</td>
          <td>${esc(duration(run.duration_sec))}</td>
        </tr>
      `).join('') : emptyRow(5, 'Ainda não há runs recebidas.');
      $$('[data-run-id]', body).forEach((row) => {
        row.addEventListener('click', async () => {
          $$('[data-run-id]', body).forEach((item) => item.classList.remove('is-selected'));
          row.classList.add('is-selected');
          await selectRun(row.dataset.runId);
        });
      });
    }
    await selectRun(runs[0]?.run_id);
    setSync('Sincronizado', 'ok');
  } catch (error) {
    setSync('Erro', 'danger');
    setAlert(error.message, 'error');
  }
}

function latestModuleStatus(modules) {
  const latest = new Map();
  modules.forEach((item) => {
    if (!latest.has(item.module_id)) latest.set(item.module_id, item);
  });
  return latest;
}

async function loadLineage() {
  setSync('A carregar');
  setAlert();
  try {
    const [pipelinesResponse, databaseResponse] = await Promise.all([
      api('/v1/read/pipelines'),
      api('/v1/read/database'),
    ]);
    renderDatabase(databaseResponse.database);
    state.pipelines = pipelinesResponse.items || [];
    const select = $('[data-pipeline-select]');
    if (select) {
      select.innerHTML = state.pipelines.length ? state.pipelines.map((item) => `
        <option value="${esc(item.pipeline_id)}">${esc(item.pipeline_id)}</option>
      `).join('') : '<option value="">Sem pipelines</option>';
      if (!state.selectedPipelineId && state.pipelines[0]) state.selectedPipelineId = state.pipelines[0].pipeline_id;
      select.value = state.selectedPipelineId;
      select.onchange = () => {
        state.selectedPipelineId = select.value;
        sessionStorage.setItem('overseer_selected_pipeline', state.selectedPipelineId);
        loadLineage();
      };
    }
    if (!state.selectedPipelineId) {
      renderDag(null, [], []);
      setSync('Sem catálogo', 'warn');
      return;
    }
    const [dagResponse, modulesResponse] = await Promise.all([
      api(`/v1/read/pipelines/${encodeURIComponent(state.selectedPipelineId)}/dag`),
      api(`/v1/read/modules?pipeline_id=${encodeURIComponent(state.selectedPipelineId)}`),
    ]);
    renderDag(dagResponse.dag, dagResponse.dag?.nodes || [], modulesResponse.items || []);
    setSync('Sincronizado', 'ok');
  } catch (error) {
    setSync('Erro', 'danger');
    setAlert(error.message, 'error');
  }
}

function renderDag(dag, nodes, modules) {
  setText('[data-dag-title]', dag?.pipeline?.name || dag?.pipeline?.pipeline_id || 'DAG');
  setText('[data-count="nodes"]', `${nodes.length} node(s)`);
  setText('[data-count="edges"]', `${dag?.edges?.length || 0} edge(s)`);
  const latest = latestModuleStatus(modules);
  const board = $('[data-dag-board]');
  if (board) {
    board.innerHTML = nodes.length ? nodes.map((node) => {
      const runtime = latest.get(node.module_id);
      const klass = runtime?.status || '';
      return `
        <div class="dag-node ${statusClass(klass)}">
          <strong>${esc(node.label || node.module_id)}</strong>
          <span>${esc(node.module_id)}</span>
          <span class="pill ${statusClass(klass)}">${esc(statusLabel(runtime?.status || 'sem runtime'))}</span>
        </div>
      `;
    }).join('') : emptyBlock('Ainda não há nodes registados para este pipeline.');
  }
  const edges = $('[data-dag-edges]');
  if (edges) {
    edges.innerHTML = dag?.edges?.length ? dag.edges.map((edge) => `
      <div class="alert-item">
        <div><strong>${esc(edge.from_module_id)}</strong><p>${esc(edge.to_module_id)}</p></div>
        <span class="pill">edge</span>
      </div>
    `).join('') : emptyBlock('Ainda não há dependências registadas.');
  }
}

async function loadDeployments() {
  setSync('A carregar');
  setAlert();
  try {
    const [databaseResponse, heartbeatsResponse, triggersResponse] = await Promise.all([
      api('/v1/read/database'),
      api('/v1/read/heartbeats?limit=50'),
      api('/v1/read/triggers?limit=50'),
    ]);
    renderDatabase(databaseResponse.database);
    const heartbeats = heartbeatsResponse.items || [];
    const triggers = triggersResponse.items || [];
    setText('[data-count="heartbeats"]', `${heartbeats.length} heartbeat(s)`);
    setText('[data-count="triggers"]', `${triggers.length} trigger(s)`);
    const heartbeatBox = $('[data-heartbeats]');
    if (heartbeatBox) {
      heartbeatBox.innerHTML = heartbeats.length ? heartbeats.map((item) => `
        <div class="alert-item">
          <div><strong>${esc(item.source_id)}</strong><p>${esc(item.pipeline_id || item.source_type)} · ${esc(formatDate(item.seen_at))}</p></div>
          <span class="pill ${statusClass(item.status)}">${esc(statusLabel(item.status))}</span>
        </div>
      `).join('') : emptyBlock('Ainda não há heartbeats.');
    }
    const triggerBox = $('[data-triggers]');
    if (triggerBox) {
      triggerBox.innerHTML = triggers.length ? triggers.map((item) => `
        <div class="alert-item">
          <div><strong>${esc(item.pipeline_id)}</strong><p>${esc(item.trigger_id)} · ${esc(formatDate(item.created_at))}</p></div>
          <span class="pill ${statusClass(item.status)}">${esc(statusLabel(item.status))}</span>
        </div>
      `).join('') : emptyBlock('Ainda não há triggers.');
    }
    setSync('Sincronizado', 'ok');
  } catch (error) {
    setSync('Erro', 'danger');
    setAlert(error.message, 'error');
  }
}

function init() {
  const view = document.body.dataset.view;
  const loaders = {
    dashboard: loadDashboard,
    runs: loadRuns,
    lineage: loadLineage,
    deployments: loadDeployments,
  };
  const load = loaders[view] || loadDashboard;
  bindChrome(load);
  load();
}

init();
