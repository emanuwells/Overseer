import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { Alert, EmptyState } from '../components/ui/Alert';
import { PipelineLabel } from '../components/ui/PipelineLabel';
import { Pill } from '../components/ui/Pill';
import { TokenBanner } from '../components/ui/TokenBanner';
import { api } from '../lib/api';
import type { DatabaseInfo, Pipeline, Run, RunDetail } from '../lib/types';
import {
  dedupePipelines,
  deploymentStaleFlag,
  duration,
  formatDate,
  isStaleRun,
  pipelineLabel,
  statusClass,
  statusLabel,
} from '../lib/utils';

export function RunsPage() {
  const [params, setParams] = useSearchParams();
  const filterPipeline = params.get('pipeline') || '';
  const filterHost = params.get('host') || '';
  const requestedRun = params.get('run') || '';

  const listQuery = useQuery({
    queryKey: ['runs', filterPipeline, filterHost],
    queryFn: async () => {
      const runsQuery = new URLSearchParams({ limit: '80' });
      if (filterPipeline) runsQuery.set('pipeline_id', filterPipeline);
      if (filterHost) runsQuery.set('host_id', filterHost);
      const [runsResponse, pipelinesResponse, database] = await Promise.all([
        api<{ items: Run[] }>(`/v1/read/runs?${runsQuery.toString()}`),
        api<{ items: Pipeline[] }>('/v1/read/pipelines'),
        api<{ database: DatabaseInfo }>('/v1/read/database'),
      ]);
      const runs = runsResponse.items || [];
      const pipelines = dedupePipelines(pipelinesResponse.items || []);
      const run = runs.find((item) => item.run_id === requestedRun) || runs[0];
      return { runs, pipelines, database: database.database, selectedRunId: run?.run_id };
    },
  });

  const detailQuery = useQuery({
    queryKey: ['run-detail', listQuery.data?.selectedRunId],
    enabled: Boolean(listQuery.data?.selectedRunId),
    queryFn: () =>
      api<RunDetail>(`/v1/read/runs/${encodeURIComponent(listQuery.data!.selectedRunId!)}`),
  });

  const runs = listQuery.data?.runs || [];
  const pipelines = listQuery.data?.pipelines || [];
  const selectedRunId = listQuery.data?.selectedRunId;
  const detail = detailQuery.data;
  const run = detail?.run;
  const modules = detail?.modules || [];
  const logs = detail?.logs || [];

  const filteredRuns = useMemo(() => runs, [runs]);

  const selectRun = (runId: string) => {
    const next = new URLSearchParams(params);
    next.set('run', runId);
    setParams(next);
  };

  return (
    <AppShell
      title="Histórico de runs"
      breadcrumb={run ? `Runs / ${pipelineLabel(run, '', '', pipelines).title}` : 'Runs'}
      database={listQuery.data?.database}
      syncLabel={
        listQuery.isFetching || detailQuery.isFetching
          ? 'A carregar'
          : listQuery.isError || detailQuery.isError
            ? 'Erro'
            : runs.length
              ? 'Sincronizado'
              : 'Sem runs'
      }
      syncKind={listQuery.isError || detailQuery.isError ? 'danger' : runs.length ? 'ok' : 'warn'}
      onRefresh={() => {
        listQuery.refetch();
        detailQuery.refetch();
      }}
    >
      <TokenBanner />
      {(listQuery.isError || detailQuery.isError) && (
        <Alert message={((listQuery.error || detailQuery.error) as Error).message} />
      )}

      <div className="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="rounded-xl border border-slate-800 bg-slate-900/40 p-3">
          <p className="mb-3 text-xs text-slate-500">{runs.length} run(s) recente(s).</p>
          {filteredRuns.length ? (
            <div className="max-h-[70vh] space-y-1 overflow-y-auto">
              {filteredRuns.map((item) => {
                const dep = pipelines.find(
                  (p) => p.pipeline_id === item.pipeline_id && (p.host_id || '') === (item.host_id || ''),
                );
                const stale = isStaleRun(
                  item.started_at,
                  item.status,
                  deploymentStaleFlag(dep),
                  dep?.schedule,
                );
                const klass = stale ? 'stale' : statusClass(item.status);
                return (
                  <button
                    key={item.run_id}
                    type="button"
                    onClick={() => selectRun(item.run_id)}
                    className={`w-full rounded-lg border px-3 py-2 text-left ${
                      item.run_id === selectedRunId
                        ? 'border-blue-500/50 bg-blue-500/10'
                        : 'border-slate-800 hover:border-slate-600'
                    }`}
                  >
                    <PipelineLabel source={item} pipelines={pipelines} />
                    <div className="mt-1 flex items-center justify-between font-mono text-xs text-slate-500">
                      <span>{formatDate(item.started_at)}</span>
                      <Pill kind={klass}>{stale ? 'stale' : statusLabel(item.status)}</Pill>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <EmptyState>Sem runs registadas.</EmptyState>
          )}
        </aside>

        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          {run ? (
            <>
              <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
                <div>
                  <PipelineLabel source={run} pipelines={pipelines} />
                  <p className="mt-1 font-mono text-sm text-slate-400">
                    {run.run_id} · {run.status}
                  </p>
                </div>
                <Pill kind={statusClass(run.status)}>{run.status}</Pill>
              </div>
              <div className="mb-4 grid gap-3 sm:grid-cols-3">
                <div className="rounded-lg border border-slate-800 p-3">
                  <span className="text-xs text-slate-500">Início</span>
                  <p className="font-mono text-sm">{formatDate(run.started_at)}</p>
                </div>
                <div className="rounded-lg border border-slate-800 p-3">
                  <span className="text-xs text-slate-500">Duração</span>
                  <p className="font-mono text-sm">{duration(run.duration_sec)}</p>
                </div>
                <div className="rounded-lg border border-slate-800 p-3">
                  <span className="text-xs text-slate-500">Módulos / Logs</span>
                  <p className="font-mono text-sm">
                    {modules.length} / {logs.length}
                  </p>
                </div>
              </div>

              <h3 className="mb-2 font-medium">Módulos</h3>
              <div className="mb-6 overflow-x-auto">
                <table className="w-full min-w-[600px] text-sm">
                  <thead className="border-b border-slate-800 text-xs text-slate-500">
                    <tr>
                      {['Módulo', 'Estado', 'Início', 'Duração', 'Erro'].map((h) => (
                        <th key={h} className="px-2 py-2 text-left">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {modules.length ? (
                      modules.map((item) => (
                        <tr key={item.module_id} className="border-b border-slate-800/80">
                          <td className="px-2 py-2">{item.module_id}</td>
                          <td className="px-2 py-2">
                            <Pill kind={statusClass(item.status)}>{statusLabel(item.status)}</Pill>
                          </td>
                          <td className="px-2 py-2 font-mono text-xs">{formatDate(item.started_at)}</td>
                          <td className="px-2 py-2 font-mono text-xs">{duration(item.duration_sec)}</td>
                          <td className="px-2 py-2 text-xs">{item.error_message || '--'}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="px-2 py-4 text-center text-slate-500">
                          Sem módulos registados para esta run.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              <h3 className="mb-2 font-medium">Logs</h3>
              <div className="max-h-80 space-y-1 overflow-y-auto rounded-lg border border-slate-800 bg-slate-950/50 p-2 font-mono text-xs">
                {logs.length ? (
                  logs.slice(0, 50).map((item, index) => (
                    <div key={index} className="grid grid-cols-[120px_60px_1fr] gap-2 border-b border-slate-800/50 py-1">
                      <span className="text-slate-500">{formatDate(item.created_at)}</span>
                      <span>{item.level}</span>
                      <span>{item.message}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-slate-500">Sem logs registados.</div>
                )}
              </div>
            </>
          ) : (
            <EmptyState>Sem run selecionada.</EmptyState>
          )}
        </section>
      </div>
    </AppShell>
  );
}
