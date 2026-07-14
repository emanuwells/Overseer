import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { Alert, EmptyState } from '../components/ui/Alert';
import { DbStatusMobile } from '../components/ui/DbStatus';
import { PipelineLabel } from '../components/ui/PipelineLabel';
import { Pill } from '../components/ui/Pill';
import { TokenBanner } from '../components/ui/TokenBanner';
import { api } from '../lib/api';
import type { DatabaseInfo, OverviewData, Pipeline, Run } from '../lib/types';
import {
  criticalityClass,
  dedupePipelines,
  deploymentShowsStale,
  duration,
  effectiveHostId,
  formatDate,
  hostDisplay,
  hostKeyMatch,
  isStaleRun,
  pipelineLabel,
  runDeploymentKey,
  stateBucket,
  statusClass,
  statusLabel,
} from '../lib/utils';

function InspectorPanel({
  item,
  recentRuns,
}: {
  item: Pipeline | null;
  recentRuns: Run[];
}) {
  if (!item) {
    return (
      <aside className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <EmptyState>Selecciona um pipeline na tabela.</EmptyState>
      </aside>
    );
  }

  const key = `${item.pipeline_id}::${item.host_id || ''}`;
  const runs = recentRuns
    .filter((run) => runDeploymentKey(run) === key)
    .sort((a, b) => new Date(b.started_at || 0).getTime() - new Date(a.started_at || 0).getTime())
    .slice(0, 8);

  return (
    <aside className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">
            {pipelineLabel(item).title} · {hostDisplay(item)}
          </h2>
          <p className="text-sm text-slate-400">{statusLabel(item.last_status)}</p>
        </div>
        <Link
          to={`/dag?pipeline=${encodeURIComponent(item.pipeline_id)}&host=${encodeURIComponent(item.host_id || '')}`}
          className="rounded-lg border border-slate-600 px-2.5 py-1 text-xs hover:bg-slate-800"
        >
          Ver DAG
        </Link>
      </div>
      <p className="mb-3 text-xs text-slate-500">Runs recentes deste deployment</p>
      <Link
        to={`/runs?pipeline=${encodeURIComponent(item.pipeline_id)}&host=${encodeURIComponent(item.host_id || '')}`}
        className="mb-3 inline-block text-xs text-blue-300 hover:underline"
      >
        Ver todas as runs
      </Link>
      {runs.length ? (
        <div className="space-y-2">
          {runs.map((run) => {
            const stale = isStaleRun(run.started_at, run.status, false, item.schedule);
            const klass = stale ? 'stale' : statusClass(run.status);
            return (
              <Link
                key={run.run_id}
                to={`/runs?run=${encodeURIComponent(run.run_id)}&pipeline=${encodeURIComponent(item.pipeline_id)}&host=${encodeURIComponent(item.host_id || '')}`}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2 hover:border-slate-600"
              >
                <div>
                  <strong className="text-sm">{run.run_id}</strong>
                  <p className="font-mono text-xs text-slate-500">
                    {formatDate(run.started_at)} · {duration(run.duration_sec)}
                  </p>
                </div>
                <Pill kind={klass}>{stale ? 'stale' : statusLabel(run.status)}</Pill>
              </Link>
            );
          })}
        </div>
      ) : (
        <EmptyState>Sem runs para este deployment.</EmptyState>
      )}
    </aside>
  );
}

export function OperationsPage() {
  const [hostFilter, setHostFilter] = useState('all');
  const [stateFilter, setStateFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Pipeline | null>(null);

  const query = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const [overview, database] = await Promise.all([
        api<{ data: OverviewData }>('/v1/read/overview'),
        api<{ database: DatabaseInfo }>('/v1/read/database'),
      ]);
      return { overview: overview.data, database: database.database };
    },
  });

  const pipelines = useMemo(
    () => dedupePipelines(query.data?.overview?.pipelines || []),
    [query.data?.overview?.pipelines],
  );

  const hosts = useMemo(
    () =>
      [...new Set(pipelines.map((item) => effectiveHostId(item)).filter(Boolean))].sort(),
    [pipelines],
  );

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return pipelines.filter((item) => {
      const label = pipelineLabel(item);
      const hostOk = hostFilter === 'all' || hostKeyMatch(effectiveHostId(item), hostFilter);
      const stateOk = stateFilter === 'all' || stateBucket(item.last_status) === stateFilter;
      const text = `${label.title} ${label.subtitle} ${effectiveHostId(item)} ${item.owner}`.toLowerCase();
      const searchOk = !q || text.includes(q);
      return hostOk && stateOk && searchOk;
    });
  }, [pipelines, hostFilter, stateFilter, search]);

  const summary = query.data?.overview?.summary;
  const database = query.data?.database;
  const recentRuns = query.data?.overview?.recent_runs || [];

  return (
    <AppShell
      title="Operações de pipelines"
      breadcrumb="Operações"
      database={database}
      syncLabel={query.isFetching ? 'A carregar' : query.isError ? 'Erro' : 'Sincronizado'}
      syncKind={query.isError ? 'danger' : query.isFetching ? '' : 'ok'}
      onRefresh={() => query.refetch()}
      actions={
        <>
          <DbStatusMobile database={database} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Pesquisar pipeline ou host"
            className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm"
          />
          <select
            value={stateFilter}
            onChange={(e) => setStateFilter(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-sm"
          >
            <option value="all">todos</option>
            <option value="ok">ok</option>
            <option value="warn">atenção</option>
            <option value="danger">falha</option>
          </select>
        </>
      }
    >
      <p className="mb-4 text-sm text-slate-400">
        Estado por deployment (pipeline + host). Interface read-only — alterações via runners e CLI.
      </p>
      <TokenBanner />
      {query.isError && <Alert message={(query.error as Error).message} />}
      {database && !database.reachable && (
        <Alert message="Base de dados indisponível." />
      )}

      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { label: 'Deployments', value: summary?.pipelines ?? 0, hint: 'catálogo' },
          { label: 'Runs', value: summary?.runs ?? 0, hint: 'histórico', to: '/runs' },
          { label: 'Falhas', value: summary?.failed ?? 0, hint: 'últimas runs', danger: true },
          { label: 'Sucesso', value: `${summary?.success_rate ?? 0}%`, hint: 'taxa' },
        ].map((kpi) => (
          <div
            key={kpi.label}
            className="rounded-xl border border-slate-800 bg-slate-900/50 p-4"
          >
            <span className="text-xs text-slate-500">{kpi.label}</span>
            <div className="mt-2 flex items-baseline gap-2">
              {kpi.to ? (
                <Link to={kpi.to} className="font-mono text-2xl font-semibold hover:text-blue-300">
                  {kpi.value}
                </Link>
              ) : (
                <span className="font-mono text-2xl font-semibold">{kpi.value}</span>
              )}
              <span className={`text-xs ${kpi.danger ? 'text-rose-400' : 'text-slate-500'}`}>
                {kpi.hint}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="font-semibold">Pipelines por host</h2>
              <p className="text-sm text-slate-500">{pipelines.length} deployment(s) activo(s).</p>
            </div>
            <Link to="/runs" className="rounded-lg border border-slate-600 px-3 py-1.5 text-sm hover:bg-slate-800">
              Ver todas as runs
            </Link>
          </div>
          <div className="mb-3 flex flex-wrap gap-2">
            {[{ id: 'all', label: 'Todos' }, ...hosts.map((h) => ({ id: h, label: h }))].map(
              (chip) => (
                <button
                  key={chip.id}
                  type="button"
                  onClick={() => setHostFilter(chip.id)}
                  className={`rounded-full border px-3 py-1 text-xs ${
                    hostFilter === chip.id
                      ? 'border-blue-500/50 bg-blue-500/15 text-blue-200'
                      : 'border-slate-700 text-slate-400 hover:border-slate-500'
                  }`}
                >
                  {chip.label}
                </button>
              ),
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b border-slate-800 text-xs uppercase text-slate-500">
                <tr>
                  {['Pipeline', 'Host', 'Estado', 'Dono', 'Agenda', 'Última run', 'Duração', 'Criticidade'].map(
                    (h) => (
                      <th key={h} className="px-2 py-2 font-medium">
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {filtered.length ? (
                  filtered.map((item) => {
                    const stale = deploymentShowsStale(item);
                    const statusKlass = stale ? 'stale' : statusClass(item.last_status);
                    const statusText = stale ? 'stale' : statusLabel(item.last_status);
                    const isSelected =
                      selected?.pipeline_id === item.pipeline_id &&
                      selected?.host_id === item.host_id;
                    return (
                      <tr
                        key={`${item.pipeline_id}::${item.host_id}`}
                        onClick={() => setSelected(item)}
                        className={`cursor-pointer border-b border-slate-800/80 hover:bg-slate-800/40 ${
                          isSelected ? 'bg-blue-500/10' : ''
                        }`}
                      >
                        <td className="px-2 py-2">
                          <Link
                            to={`/dag?pipeline=${encodeURIComponent(item.pipeline_id)}&host=${encodeURIComponent(item.host_id || '')}`}
                            onClick={(e) => e.stopPropagation()}
                            className="flex items-center gap-2"
                          >
                            <span
                              className={`h-2 w-2 rounded-full ${
                                statusKlass === 'ok'
                                  ? 'bg-emerald-400'
                                  : statusKlass === 'danger'
                                    ? 'bg-rose-400'
                                    : statusKlass === 'stale'
                                      ? 'bg-orange-400'
                                      : 'bg-amber-400'
                              }`}
                            />
                            <PipelineLabel source={item} />
                          </Link>
                        </td>
                        <td className="px-2 py-2">{hostDisplay(item)}</td>
                        <td className="px-2 py-2">
                          <Pill kind={statusKlass}>{statusText}</Pill>
                        </td>
                        <td className="px-2 py-2">{item.owner}</td>
                        <td className="px-2 py-2 font-mono text-xs">{item.schedule}</td>
                        <td className="px-2 py-2 font-mono text-xs">{formatDate(item.last_started_at)}</td>
                        <td className="px-2 py-2 font-mono text-xs">{duration(item.last_duration_sec)}</td>
                        <td className="px-2 py-2">
                          <Pill kind={criticalityClass(item.criticality)}>{item.criticality}</Pill>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={8} className="px-2 py-6 text-center text-slate-500">
                      Ainda não há deployments. Verifica o catálogo YAML ou telemetria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
        <InspectorPanel item={selected || filtered[0] || null} recentRuns={recentRuns} />
      </div>
    </AppShell>
  );
}
