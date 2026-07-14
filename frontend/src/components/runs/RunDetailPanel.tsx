import { PipelineLabel } from '../ui/PipelineLabel';
import { Pill } from '../ui/Pill';
import type { Pipeline, Run, RunLog, RunModule } from '../../lib/types';
import { duration, formatDate, statusClass, statusLabel } from '../../lib/utils';

export function RunDetailPanel({
  run,
  modules,
  logs,
  pipelines,
}: {
  run: Run;
  modules: RunModule[];
  logs: RunLog[];
  pipelines: Pipeline[];
}) {
  return (
    <>
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <PipelineLabel source={run} pipelines={pipelines} />
          <p className="mt-1 font-mono text-sm text-slate-400">
            {run.run_id} · {run.status}
          </p>
        </div>
        <Pill kind={statusClass(run.status)}>{statusLabel(run.status)}</Pill>
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
            <div
              key={index}
              className="grid grid-cols-[120px_60px_1fr] gap-2 border-b border-slate-800/50 py-1"
            >
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
  );
}
