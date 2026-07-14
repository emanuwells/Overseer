import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { RunDetailPanel } from '../components/runs/RunDetailPanel';
import { Alert, EmptyState } from '../components/ui/Alert';
import { Modal } from '../components/ui/Modal';
import { PipelineLabel } from '../components/ui/PipelineLabel';
import { Pill } from '../components/ui/Pill';
import { TokenBanner } from '../components/ui/TokenBanner';
import { api } from '../lib/api';
import type { DatabaseInfo, Pipeline, Run, RunDetail } from '../lib/types';
import {
  dedupePipelines,
  deploymentStaleFlag,
  formatDate,
  isStaleRun,
  pipelineLabel,
  statusClass,
  statusLabel,
} from '../lib/utils';

export function RunsPage() {
  const [params, setParams] = useSearchParams();
  const [modalOpen, setModalOpen] = useState(false);
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

  const deploymentLabel = useMemo(() => {
    if (!filterPipeline) return undefined;
    const dep = pipelines.find(
      (p) => p.pipeline_id === filterPipeline && (p.host_id || '') === filterHost,
    );
    if (dep) return pipelineLabel(dep).title;
    const first = runs.find((r) => r.pipeline_id === filterPipeline);
    return first ? pipelineLabel(first, filterPipeline, filterHost, pipelines).title : filterPipeline;
  }, [filterPipeline, filterHost, pipelines, runs]);

  const selectRun = (runId: string) => {
    const next = new URLSearchParams(params);
    next.set('run', runId);
    setParams(next);
    if (typeof window !== 'undefined' && window.matchMedia('(max-width: 1023px)').matches) {
      setModalOpen(true);
    }
  };

  return (
    <AppShell
      title="Histórico de runs"
      breadcrumb={
        run
          ? `Runs / ${pipelineLabel(run, '', '', pipelines).title}`
          : deploymentLabel
            ? `Runs / ${deploymentLabel}`
            : 'Runs'
      }
      deploymentContext={
        filterPipeline
          ? { pipelineId: filterPipeline, hostId: filterHost, label: deploymentLabel }
          : undefined
      }
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
                    className={`w-full rounded-lg border px-3 py-2 text-left lg:pointer-events-auto ${
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

        <section className="hidden rounded-xl border border-slate-800 bg-slate-900/40 p-4 lg:block">
          {run ? (
            <RunDetailPanel run={run} modules={modules} logs={logs} pipelines={pipelines} />
          ) : (
            <EmptyState>Sem run selecionada.</EmptyState>
          )}
        </section>
      </div>

      <Modal
        open={modalOpen && Boolean(run)}
        title="Detalhe da run"
        wide
        onClose={() => setModalOpen(false)}
      >
        {run ? (
          <RunDetailPanel run={run} modules={modules} logs={logs} pipelines={pipelines} />
        ) : detailQuery.isLoading ? (
          <p className="text-sm text-slate-400">A carregar…</p>
        ) : null}
      </Modal>
    </AppShell>
  );
}
