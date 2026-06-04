import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  Clock,
  Database,
  GitBranch,
  HardDrive,
  ListChecks,
  Play,
  Radio,
  RefreshCw,
  Search,
  Shield,
  Terminal,
  XCircle,
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

function formatTime(value) {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return new Intl.DateTimeFormat('pt-PT', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    day: '2-digit',
    month: '2-digit',
  }).format(date);
}

function formatDuration(value) {
  if (value === null || value === undefined || value === '') return '-';
  const seconds = Number(value);
  if (Number.isNaN(seconds)) return '-';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

function statusTone(value) {
  const normalized = String(value || 'unknown').toLowerCase();
  if (['ok', 'success', 'completed', 'done'].includes(normalized)) return 'ok';
  if (['failed', 'error', 'erro'].includes(normalized)) return 'failed';
  if (['warning', 'warn'].includes(normalized)) return 'warning';
  if (['running', 'started', 'claimed'].includes(normalized)) return 'running';
  if (['queued'].includes(normalized)) return 'queued';
  return 'unknown';
}

function Status({ value }) {
  const tone = statusTone(value);
  const Icon = tone === 'ok' ? CheckCircle2 : tone === 'failed' ? XCircle : tone === 'warning' ? AlertTriangle : CircleDot;
  return (
    <span className={`status status-${tone}`}>
      <Icon size={13} />
      {String(value || 'unknown').toLowerCase()}
    </span>
  );
}

function Metric({ icon: Icon, label, value, tone = 'neutral', caption }) {
  return (
    <div className={`metric metric-${tone}`}>
      <span className="metric-label"><Icon size={15} /> {label}</span>
      <strong>{value}</strong>
      <small>{caption || '\u00a0'}</small>
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

function Panel({ title, meta, children, className = '' }) {
  return (
    <section className={`panel ${className}`}>
      <div className="panel-heading">
        <h3>{title}</h3>
        <span>{meta}</span>
      </div>
      {children}
    </section>
  );
}

function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem('overseer_api_token') || '');
  const [overview, setOverview] = useState(null);
  const [database, setDatabase] = useState(null);
  const [runs, setRuns] = useState([]);
  const [logs, setLogs] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [detail, setDetail] = useState(null);
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setBusy(true);
    setError('');
    try {
      const [overviewData, runsData, dbData, logsData] = await Promise.all([
        api('/v1/read/overview', { token }),
        api('/v1/read/runs?limit=200', { token }),
        api('/v1/read/database', { token }),
        api('/v1/read/logs?limit=120', { token }),
      ]);
      setOverview(overviewData.data);
      setRuns(runsData.items || []);
      setDatabase(dbData.database);
      setLogs(logsData.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }, [token]);

  useEffect(() => {
    refresh();
    const id = window.setInterval(refresh, 12000);
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

  async function runPipeline(pipelineId, background = true) {
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
  const triggers = overview?.triggers || [];
  const heartbeats = overview?.heartbeats || [];
  const latestRun = runs[0];

  const filteredRuns = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return runs;
    return runs.filter((run) => [run.pipeline_id, run.run_id, run.status, run.requested_by, run.hostname].some((value) => String(value || '').toLowerCase().includes(needle)));
  }, [query, runs]);

  const lanes = useMemo(() => {
    const base = { running: [], queued: [], ok: [], warning: [], failed: [] };
    for (const run of runs) {
      const tone = statusTone(run.status);
      if (base[tone]) base[tone].push(run);
    }
    return base;
  }, [runs]);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><Activity size={23} /></div>
          <div>
            <h1>Overseer</h1>
            <span>Control plane</span>
          </div>
        </div>
        <nav>
          <a href="#overview"><HardDrive size={16} /> Overview</a>
          <a href="#pipelines"><GitBranch size={16} /> DAGs</a>
          <a href="#runs"><ListChecks size={16} /> Runs</a>
          <a href="#logs"><Terminal size={16} /> Logs</a>
          <a href="#auth"><Shield size={16} /> Token</a>
        </nav>
        <div className="side-status">
          <span>DB</span>
          <Status value={database?.reachable ? 'ok' : 'failed'} />
          <small>{database?.database || '-'}</small>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <h2>Pipeline Operations</h2>
            <p>{latestRun ? `${latestRun.pipeline_id} · ${latestRun.status} · ${formatTime(latestRun.started_at)}` : 'Sem runs registadas'}</p>
          </div>
          <div className="toolbar">
            <div className="search">
              <Search size={16} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filtrar runs" />
            </div>
            <IconButton icon={RefreshCw} label="Atualizar" onClick={refresh} disabled={busy} />
          </div>
        </header>

        {error ? <div className="alert"><AlertTriangle size={16} /> {error}</div> : null}

        <section id="overview" className="metrics-grid">
          <Metric icon={GitBranch} label="DAGs" value={summary.pipelines ?? 0} caption={`${pipelines.length} registados`} />
          <Metric icon={ListChecks} label="Runs" value={summary.runs ?? 0} caption="histórico visível" />
          <Metric icon={Clock} label="Running" value={summary.running ?? 0} tone="running" caption="em execução" />
          <Metric icon={CheckCircle2} label="Sucesso" value={`${summary.success_rate ?? 100}%`} tone="ok" caption={`${summary.ok ?? 0} OK`} />
          <Metric icon={XCircle} label="Falhas" value={summary.failed ?? 0} tone="failed" caption={`${summary.warning ?? 0} warnings`} />
          <Metric icon={Database} label="DB" value={database?.mode || '-'} tone={database?.reachable ? 'ok' : 'failed'} caption={database?.url || '-'} />
        </section>

        <section className="lanes">
          {Object.entries(lanes).map(([lane, items]) => (
            <div className={`lane lane-${lane}`} key={lane}>
              <div className="lane-head">
                <span>{lane}</span>
                <strong>{items.length}</strong>
              </div>
              {items.slice(0, 3).map((run) => (
                <button type="button" key={run.run_id} onClick={() => openRun(run.run_id)} className="lane-card">
                  <strong>{run.pipeline_id}</strong>
                  <small>{formatTime(run.started_at)} · {formatDuration(run.duration_sec)}</small>
                </button>
              ))}
            </div>
          ))}
        </section>

        <section id="pipelines" className="grid-2">
          <Panel title="DAGs" meta={`${pipelines.length} pipelines`}>
            <div className="dag-list">
              {pipelines.map((pipeline) => (
                <div className="dag-row" key={pipeline.pipeline_id}>
                  <div>
                    <strong>{pipeline.name}</strong>
                    <small>{pipeline.pipeline_id} · {pipeline.owner} · {pipeline.criticality}</small>
                  </div>
                  <Status value={pipeline.last_status || 'unknown'} />
                  <div className="actions">
                    <IconButton icon={Play} label="Executar" onClick={() => runPipeline(pipeline.pipeline_id, true)} />
                    <IconButton icon={Radio} label="Trigger" onClick={() => triggerPipeline(pipeline.pipeline_id)} />
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="Base de dados" meta={database?.reachable ? 'ligada' : 'indisponível'}>
            <dl className="db-grid">
              <div><dt>Modo</dt><dd>{database?.mode || '-'}</dd></div>
              <div><dt>Driver</dt><dd>{database?.driver || '-'}</dd></div>
              <div><dt>Schema</dt><dd>{database?.database || '-'}</dd></div>
              <div><dt>Host</dt><dd>{database?.host || '-'}</dd></div>
            </dl>
            <div className="table-counts">
              {Object.entries(database?.tables || {}).map(([table, count]) => (
                <span key={table}>{table}<strong>{count}</strong></span>
              ))}
            </div>
          </Panel>
        </section>

        <section id="runs" className="split">
          <Panel title="Runs" meta={`${filteredRuns.length} visíveis`} className="runs-panel">
            <div className="run-table">
              <div className="run-table-head">
                <span>Pipeline</span><span>Estado</span><span>Início</span><span>Duração</span><span>Host</span>
              </div>
              {filteredRuns.map((run) => (
                <button type="button" className={`run-table-row ${selectedRun === run.run_id ? 'selected' : ''}`} key={run.run_id} onClick={() => openRun(run.run_id)}>
                  <span><strong>{run.pipeline_id}</strong><small>{run.run_id}</small></span>
                  <Status value={run.status} />
                  <span>{formatTime(run.started_at)}</span>
                  <span>{formatDuration(run.duration_sec)}</span>
                  <span>{run.hostname || '-'}</span>
                </button>
              ))}
            </div>
          </Panel>

          <Panel title="Detalhe da run" meta={selectedRun || '-'} className="detail-panel">
            {detail?.run ? (
              <>
                <dl className="detail-grid">
                  <div><dt>Pipeline</dt><dd>{detail.run.pipeline_id}</dd></div>
                  <div><dt>Estado</dt><dd><Status value={detail.run.status} /></dd></div>
                  <div><dt>Duração</dt><dd>{formatDuration(detail.run.duration_sec)}</dd></div>
                  <div><dt>Trigger</dt><dd>{detail.run.trigger_type}</dd></div>
                </dl>
                <div className="module-flow">
                  {(detail.modules || []).slice().reverse().map((module) => (
                    <div className={`module-node module-${statusTone(module.status)}`} key={module.event_id}>
                      <span>{module.module_id}</span>
                      <Status value={module.status} />
                      <small>{formatDuration(module.duration_sec)}</small>
                    </div>
                  ))}
                </div>
                <pre>{(detail.logs || []).map((log) => `[${formatTime(log.created_at)}] ${log.level} ${log.module_id || '-'} :: ${log.message}`).join('\n') || 'Sem logs.'}</pre>
              </>
            ) : (
              <p className="empty">Seleciona uma run.</p>
            )}
          </Panel>
        </section>

        <section id="logs" className="grid-2 bottom-grid">
          <Panel title="Triggers" meta={`${triggers.length} recentes`}>
            <div className="compact-list">
              {triggers.map((trigger) => (
                <div key={trigger.trigger_id}>
                  <span>{trigger.pipeline_id}<small>{trigger.trigger_id}</small></span>
                  <Status value={trigger.status} />
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="Heartbeats e logs" meta={`${heartbeats.length} heartbeats`}>
            <div className="compact-list">
              {heartbeats.slice(0, 4).map((heartbeat) => (
                <div key={heartbeat.heartbeat_id}>
                  <span>{heartbeat.source_id}<small>{formatTime(heartbeat.seen_at)}</small></span>
                  <Status value={heartbeat.status} />
                </div>
              ))}
            </div>
            <pre>{logs.slice(0, 12).map((log) => `[${formatTime(log.created_at)}] ${log.pipeline_id || '-'} :: ${log.message}`).join('\n') || 'Sem logs.'}</pre>
          </Panel>
        </section>

        <section id="auth" className="panel token-panel">
          <div>
            <h3>API Token</h3>
            <span>{token ? 'ativo nesta sessão' : 'sem token'}</span>
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
