import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  Bell,
  Database,
  FileText,
  Pause,
  Play,
  RefreshCw,
  Shield,
  Terminal,
} from 'lucide-react';
import './styles.css';

const API_BASE = window.location.pathname.startsWith('/ui') ? '' : 'http://127.0.0.1:8090';

function tokenHeaders(token) {
  const headers = { Accept: 'application/json', 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

async function api(path, { token, method = 'GET', body } = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: tokenHeaders(token),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function Metric({ label, value, tone = 'neutral' }) {
  return (
    <div className={`metric metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function IconButton({ icon: Icon, label, onClick, disabled = false }) {
  return (
    <button type="button" className="icon-button" onClick={onClick} disabled={disabled} title={label} aria-label={label}>
      <Icon size={18} />
    </button>
  );
}

function Status({ value }) {
  const normalized = String(value || 'unknown').toLowerCase();
  return <span className={`status status-${normalized}`}>{normalized}</span>;
}

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem('overseer_api_token') || '');
  const [overview, setOverview] = useState(null);
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setBusy(true);
    setError('');
    try {
      const [overviewData, runsData] = await Promise.all([
        api('/v1/read/overview', { token }),
        api('/v1/read/runs?limit=100', { token }),
      ]);
      setOverview(overviewData.data);
      setRuns(runsData.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }, [token]);

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, 15000);
    return () => window.clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    sessionStorage.setItem('overseer_api_token', token);
  }, [token]);

  async function openRun(runId) {
    setSelectedRun(runId);
    setDetail(null);
    const data = await api(`/v1/read/runs/${runId}`, { token });
    setDetail(data);
  }

  async function runPipeline(pipelineId, background) {
    await api(`/v1/orchestrate/pipelines/${pipelineId}/run`, {
      token,
      method: 'POST',
      body: { requested_by: 'ui', background },
    });
    refresh();
  }

  async function triggerPipeline(pipelineId) {
    await api('/v1/orchestrate/triggers', {
      token,
      method: 'POST',
      body: { pipeline_id: pipelineId, requested_by: 'ui', runner_host: 'any' },
    });
    refresh();
  }

  const summary = overview?.summary || {};
  const pipelines = overview?.pipelines || [];
  const latestRun = useMemo(() => runs[0], [runs]);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <Activity size={24} />
          <div>
            <h1>Overseer</h1>
            <span>Estado da nação</span>
          </div>
        </div>
        <nav>
          <a href="#overview"><Database size={16} /> Operação</a>
          <a href="#pipelines"><Terminal size={16} /> Pipelines</a>
          <a href="#runs"><FileText size={16} /> Runs</a>
          <a href="#auth"><Shield size={16} /> Token</a>
        </nav>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <h2>Comando local</h2>
            <p>{latestRun ? `Última run: ${latestRun.pipeline_id} · ${latestRun.status}` : 'Sem runs registadas ainda'}</p>
          </div>
          <IconButton icon={RefreshCw} label="Atualizar" onClick={refresh} disabled={busy} />
        </header>

        {error ? <div className="alert"><Bell size={16} /> {error}</div> : null}

        <section id="overview" className="metrics-grid">
          <Metric label="Pipelines" value={summary.pipelines ?? 0} />
          <Metric label="Runs" value={summary.runs ?? 0} />
          <Metric label="A correr" value={summary.running ?? 0} tone="running" />
          <Metric label="OK" value={summary.ok ?? 0} tone="ok" />
          <Metric label="Falhas" value={summary.failed ?? 0} tone="failed" />
          <Metric label="Sucesso" value={`${summary.success_rate ?? 100}%`} />
        </section>

        <section id="pipelines" className="panel">
          <div className="panel-heading">
            <h3>Pipelines</h3>
            <span>{pipelines.length} registados</span>
          </div>
          <div className="table">
            <div className="table-row table-head">
              <span>Pipeline</span>
              <span>Owner</span>
              <span>Schedule</span>
              <span>Estado</span>
              <span>Ações</span>
            </div>
            {pipelines.map((pipeline) => (
              <div className="table-row" key={pipeline.pipeline_id}>
                <span>
                  <strong>{pipeline.name}</strong>
                  <small>{pipeline.pipeline_id}</small>
                </span>
                <span>{pipeline.owner}</span>
                <span>{pipeline.schedule}</span>
                <span><Status value={pipeline.last_status || 'unknown'} /></span>
                <span className="actions">
                  <IconButton icon={Play} label="Executar agora" onClick={() => runPipeline(pipeline.pipeline_id, true)} />
                  <IconButton icon={Pause} label="Enfileirar trigger" onClick={() => triggerPipeline(pipeline.pipeline_id)} />
                </span>
              </div>
            ))}
          </div>
        </section>

        <section id="runs" className="split">
          <div className="panel">
            <div className="panel-heading">
              <h3>Runs recentes</h3>
              <span>{runs.length} visíveis</span>
            </div>
            <div className="run-list">
              {runs.map((run) => (
                <button
                  type="button"
                  className={`run-row ${selectedRun === run.run_id ? 'selected' : ''}`}
                  key={run.run_id}
                  onClick={() => openRun(run.run_id)}
                >
                  <span>
                    <strong>{run.pipeline_id}</strong>
                    <small>{run.run_id}</small>
                  </span>
                  <Status value={run.status} />
                </button>
              ))}
            </div>
          </div>

          <div className="panel detail">
            <div className="panel-heading">
              <h3>Detalhe</h3>
              <span>{selectedRun || '-'}</span>
            </div>
            {detail?.run ? (
              <>
                <dl>
                  <div><dt>Pipeline</dt><dd>{detail.run.pipeline_id}</dd></div>
                  <div><dt>Estado</dt><dd><Status value={detail.run.status} /></dd></div>
                  <div><dt>Duração</dt><dd>{detail.run.duration_sec ?? '-'}s</dd></div>
                  <div><dt>Host</dt><dd>{detail.run.hostname || '-'}</dd></div>
                </dl>
                <h4>Módulos</h4>
                <div className="mini-list">
                  {(detail.modules || []).map((module) => (
                    <div key={module.event_id}>
                      <span>{module.module_id}</span>
                      <Status value={module.status} />
                    </div>
                  ))}
                </div>
                <h4>Logs</h4>
                <pre>{(detail.logs || []).map((log) => `[${log.level}] ${log.message}`).join('\n') || 'Sem logs.'}</pre>
              </>
            ) : (
              <p className="empty">Seleciona uma run para ver módulos e logs.</p>
            )}
          </div>
        </section>

        <section id="auth" className="panel token-panel">
          <div>
            <h3>API Token</h3>
            <p>Guardado apenas nesta sessão do browser.</p>
          </div>
          <input
            type="password"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="OVERSEER_API_TOKEN"
          />
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
