import { Link } from 'react-router-dom';
import { EmptyState } from '../ui/Alert';
import { Pill } from '../ui/Pill';
import type { Pipeline, Run } from '../../lib/types';
import {
  duration,
  formatDate,
  hostDisplay,
  isStaleRun,
  pipelineLabel,
  runDeploymentKey,
  statusClass,
  statusLabel,
} from '../../lib/utils';

export function PipelineInspector({
  item,
  recentRuns,
  onRunClick,
}: {
  item: Pipeline | null;
  recentRuns: Run[];
  onRunClick?: (run: Run) => void;
}) {
  if (!item) {
    return <EmptyState>Selecciona um pipeline na tabela.</EmptyState>;
  }

  const key = `${item.pipeline_id}::${item.host_id || ''}`;
  const runs = recentRuns
    .filter((run) => runDeploymentKey(run) === key)
    .sort((a, b) => new Date(b.started_at || 0).getTime() - new Date(a.started_at || 0).getTime())
    .slice(0, 8);

  return (
    <>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">
            {pipelineLabel(item).title} · {hostDisplay(item)}
          </h2>
          <p className="text-sm text-slate-400">{statusLabel(item.last_status)}</p>
        </div>
      </div>
      <div className="mb-4 flex flex-wrap gap-2">
        <Link
          to={`/dag?pipeline=${encodeURIComponent(item.pipeline_id)}&host=${encodeURIComponent(item.host_id || '')}`}
          className="rounded-lg border border-slate-600 px-2.5 py-1 text-xs hover:bg-slate-800"
        >
          Ver DAG
        </Link>
        <Link
          to={`/runs?pipeline=${encodeURIComponent(item.pipeline_id)}&host=${encodeURIComponent(item.host_id || '')}`}
          className="rounded-lg border border-slate-600 px-2.5 py-1 text-xs hover:bg-slate-800"
        >
          Ver runs
        </Link>
        <Link
          to="/environment"
          className="rounded-lg border border-slate-600 px-2.5 py-1 text-xs hover:bg-slate-800"
        >
          Ambiente
        </Link>
      </div>
      <p className="mb-3 text-xs text-slate-500">Runs recentes deste deployment</p>
      {runs.length ? (
        <div className="space-y-2">
          {runs.map((run) => {
            const stale = isStaleRun(run.started_at, run.status, false, item.schedule);
            const klass = stale ? 'stale' : statusClass(run.status);
            const inner = (
              <>
                <div>
                  <strong className="text-sm">{run.run_id}</strong>
                  <p className="font-mono text-xs text-slate-500">
                    {formatDate(run.started_at)} · {duration(run.duration_sec)}
                  </p>
                </div>
                <Pill kind={klass}>{stale ? 'stale' : statusLabel(run.status)}</Pill>
              </>
            );
            if (onRunClick) {
              return (
                <button
                  key={run.run_id}
                  type="button"
                  onClick={() => onRunClick(run)}
                  className="flex w-full items-center justify-between rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2 text-left hover:border-slate-600"
                >
                  {inner}
                </button>
              );
            }
            return (
              <Link
                key={run.run_id}
                to={`/runs?run=${encodeURIComponent(run.run_id)}&pipeline=${encodeURIComponent(item.pipeline_id)}&host=${encodeURIComponent(item.host_id || '')}`}
                className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/50 px-3 py-2 hover:border-slate-600"
              >
                {inner}
              </Link>
            );
          })}
        </div>
      ) : (
        <EmptyState>Sem runs para este deployment.</EmptyState>
      )}
    </>
  );
}
