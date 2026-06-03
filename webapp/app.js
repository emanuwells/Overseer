/**
 * Overseer standalone webapp — reads canonical API (same origin /ui).
 */
const API_BASE = (() => {
  const meta = document.querySelector('meta[name="overseer-api-base"]');
  if (meta && meta.content) return meta.content.replace(/\/$/, '');
  return '';
})();

async function apiGet(path) {
  const headers = { Accept: 'application/json' };
  const token = sessionStorage.getItem('overseer_api_token');
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function renderHealth(data) {
  const el = document.getElementById('health');
  const ok = data.ok ? 'OK' : 'Degradado';
  el.innerHTML = `<h2>Estado</h2><p class="${data.ok ? 'status-ok' : 'status-bad'}">${ok}</p>
    <p>DB: ${data.db_reachability?.overseer_api_db ? 'ligado' : 'indisponível'}</p>`;
}

function renderSummary(payload) {
  const el = document.getElementById('summary');
  const s = payload.summary || {};
  el.innerHTML = `<h2>Resumo (24h)</h2>
    <p>Runs: ${s.total_runs ?? 0} | OK: ${s.ok_runs ?? 0} | NOK: ${s.nok_runs ?? 0}</p>
    <p>Gerado: ${payload.generated_at_label || payload.generated_at || '-'}</p>`;
}

function renderPipelines(payload) {
  const list = document.getElementById('pipelineList');
  const items = payload.pipelines || [];
  if (!items.length) {
    list.textContent = 'Sem pipelines.';
    return;
  }
  list.innerHTML = items
    .slice(0, 50)
    .map(
      (p) =>
        `<div class="pipeline-row"><span>${p.name || p.pipelineId}</span>
         <span class="${(p.lastStatus || '').toUpperCase() === 'OK' ? 'status-ok' : 'status-bad'}">${p.lastStatus || '-'}</span></div>`
    )
    .join('');
}

async function refresh() {
  try {
    const health = await apiGet('/v1/health');
    renderHealth(health);
    const full = await apiGet('/v1/monitoring/full');
    renderSummary(full);
    renderPipelines(full);
  } catch (err) {
    document.getElementById('health').innerHTML = `<p class="status-bad">Erro: ${err.message}</p>`;
  }
}

document.getElementById('btnRefresh').addEventListener('click', refresh);
refresh();
