import { useQuery } from '@tanstack/react-query';
import { AppShell } from '../components/layout/AppShell';
import { Alert, EmptyState } from '../components/ui/Alert';
import { PipelineLabel } from '../components/ui/PipelineLabel';
import { Pill } from '../components/ui/Pill';
import { TokenBanner } from '../components/ui/TokenBanner';
import { api } from '../lib/api';
import type {
  DatabaseInfo,
  Heartbeat,
  RunnerHostsPayload,
  TaskSchedulerPipeline,
  TaskSchedulerSnapshot,
  Trigger,
} from '../lib/types';
import { formatDate } from '../lib/utils';

function taskSchedulerHostId(heartbeat: Heartbeat, scheduler: TaskSchedulerSnapshot): string {
  return scheduler.host_id || heartbeat.host_id || heartbeat.hostname || heartbeat.source_id || '--';
}

function taskSchedulerIssueCount(scheduler: TaskSchedulerSnapshot): number {
  const pipelineIssues = (scheduler.pipelines || []).filter(
    (item) =>
      !item.task_found ||
      (item.last_task_result !== null &&
        item.last_task_result !== undefined &&
        Number(item.last_task_result) !== 0),
  ).length;
  return pipelineIssues + (scheduler.ok === false ? 1 : 0);
}

function latestTaskSchedulerSnapshots(heartbeats: Heartbeat[]) {
  const snapshots = new Map<
    string,
    { hostId: string; heartbeat: Heartbeat; scheduler: TaskSchedulerSnapshot }
  >();
  heartbeats.forEach((heartbeat) => {
    const scheduler = heartbeat.payload?.task_scheduler;
    if (!scheduler || typeof scheduler !== 'object') return;
    const hostId = taskSchedulerHostId(heartbeat, scheduler);
    const current = snapshots.get(hostId);
    const seenAt = new Date(scheduler.collected_at || heartbeat.seen_at || 0).getTime();
    const currentSeenAt = current
      ? new Date(current.scheduler.collected_at || current.heartbeat.seen_at || 0).getTime()
      : -1;
    if (!current || seenAt >= currentSeenAt) {
      snapshots.set(hostId, { hostId, heartbeat, scheduler });
    }
  });
  return [...snapshots.values()].sort((a, b) => String(a.hostId).localeCompare(String(b.hostId)));
}

export function EnvironmentPage() {
  const query = useQuery({
    queryKey: ['environment'],
    queryFn: async () => {
      const [database, heartbeatsResponse, triggersResponse, hosts] = await Promise.all([
        api<{ database: DatabaseInfo }>('/v1/read/database'),
        api<{ items: Heartbeat[] }>('/v1/read/heartbeats?limit=50'),
        api<{ items: Trigger[] }>('/v1/read/triggers?limit=50'),
        api<RunnerHostsPayload>('/v1/read/runner-hosts').catch(() => ({
          hosts: [],
          ssh_sync_enabled: false,
        })),
      ]);
      return {
        database: database.database,
        heartbeats: heartbeatsResponse.items || [],
        triggers: triggersResponse.items || [],
        hosts,
      };
    },
  });

  const database = query.data?.database;
  const heartbeats = query.data?.heartbeats || [];
  const triggers = query.data?.triggers || [];
  const hosts = query.data?.hosts;
  const snapshots = latestTaskSchedulerSnapshots(heartbeats);
  const pipelineRows: (TaskSchedulerPipeline & { host_id: string })[] = snapshots.flatMap(
    (snapshot) =>
      (snapshot.scheduler.pipelines || []).map((pipeline) => ({
        ...pipeline,
        host_id: snapshot.hostId,
      })),
  );
  const issueCount = snapshots.reduce(
    (total, snapshot) => total + taskSchedulerIssueCount(snapshot.scheduler),
    0,
  );
  const hostSet = new Set(
    heartbeats.map((item) => item.host_id || item.hostname || item.source_id).filter(Boolean),
  );

  return (
    <AppShell
      title="Ambiente e inventário"
      breadcrumb="Ambiente"
      database={database}
      syncLabel={query.isFetching ? 'A carregar' : query.isError ? 'Erro' : 'Sincronizado'}
      syncKind={query.isError ? 'danger' : 'ok'}
      onRefresh={() => query.refetch()}
      actions={
        hosts && (
          <Pill kind={hosts.ssh_sync_enabled ? 'ok' : 'warn'}>
            {hosts.ssh_sync_enabled ? 'SSH sync activo' : 'SSH sync desactivado'}
          </Pill>
        )
      }
    >
      <TokenBanner />
      {query.isError && <Alert message={(query.error as Error).message} />}

      <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: 'Heartbeats', value: heartbeats.length },
          { label: 'OK', value: heartbeats.filter((item) => item.status === 'ok').length },
          { label: 'Triggers', value: triggers.length },
          { label: 'Hosts activos', value: hostSet.size },
        ].map((kpi) => (
          <div key={kpi.label} className="rounded-xl border border-slate-800 bg-slate-900/50 p-4">
            <span className="text-xs text-slate-500">{kpi.label}</span>
            <p className="font-mono text-2xl font-semibold">{kpi.value}</p>
          </div>
        ))}
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <h2 className="mb-3 font-semibold">Base de dados</h2>
          <p className="mb-2 font-mono text-xs text-slate-400">{database?.url || 'URL indisponível'}</p>
          <p className="mb-3 text-sm">
            Modo: <strong>{database?.mode || '--'}</strong>
          </p>
          <table className="w-full text-sm">
            <thead className="border-b border-slate-800 text-xs text-slate-500">
              <tr>
                <th className="py-2 text-left">Tabela</th>
                <th className="py-2 text-left">Registos</th>
                <th className="py-2 text-left">Estado</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(database?.tables || {}).map(([name, value]) => (
                <tr key={name} className="border-b border-slate-800/80">
                  <td className="py-2">{name}</td>
                  <td className="py-2 font-mono">{value}</td>
                  <td className="py-2">
                    <Pill kind={database?.reachable ? 'ok' : 'danger'}>
                      {database?.reachable ? 'ok' : 'erro'}
                    </Pill>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <h2 className="mb-3 font-semibold">Runner hosts</h2>
          {(hosts?.hosts || []).length ? (
            <table className="w-full text-sm">
              <thead className="border-b border-slate-800 text-xs text-slate-500">
                <tr>
                  {['Host', 'Plataforma', 'SSH', 'Repo'].map((h) => (
                    <th key={h} className="py-2 text-left">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(hosts?.hosts || []).map((host) => (
                  <tr key={host.host_id} className="border-b border-slate-800/80">
                    <td className="py-2">{host.host_id}</td>
                    <td className="py-2">{host.platform}</td>
                    <td className="py-2 font-mono text-xs">{host.ssh || '—'}</td>
                    <td className="py-2 font-mono text-xs">{host.repo_path || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <EmptyState>Sem hosts em deploy/runners/hosts.yaml.</EmptyState>
          )}
        </section>
      </div>

      <section className="mb-6 rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <h2 className="mb-3 font-semibold">Task Scheduler</h2>
        <div className="mb-4 grid gap-3 sm:grid-cols-3">
          <div>
            <span className="text-xs text-slate-500">Hosts</span>
            <p className="font-mono text-xl">{snapshots.length}</p>
          </div>
          <div>
            <span className="text-xs text-slate-500">Tasks encontradas</span>
            <p className="font-mono text-xl">
              {pipelineRows.filter((item) => item.task_found).length}
            </p>
          </div>
          <div>
            <span className="text-xs text-slate-500">Problemas</span>
            <p className="font-mono text-xl">{issueCount}</p>
          </div>
        </div>
        {snapshots.length ? (
          <table className="w-full text-sm">
            <thead className="border-b border-slate-800 text-xs text-slate-500">
              <tr>
                {['Host', 'Tasks', 'Erros', 'Recolha', 'Estado'].map((h) => (
                  <th key={h} className="py-2 text-left">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {snapshots.map((snapshot) => {
                const pipelines = snapshot.scheduler.pipelines || [];
                const issues = taskSchedulerIssueCount(snapshot.scheduler);
                const ok = snapshot.scheduler.ok !== false && issues === 0;
                return (
                  <tr key={snapshot.hostId} className="border-b border-slate-800/80">
                    <td className="py-2">{snapshot.hostId}</td>
                    <td className="py-2">
                      {pipelines.filter((item) => item.task_found).length} / {pipelines.length}
                    </td>
                    <td className="py-2">{issues}</td>
                    <td className="py-2 font-mono text-xs">
                      {formatDate(snapshot.scheduler.collected_at || snapshot.heartbeat.seen_at)}
                    </td>
                    <td className="py-2">
                      <Pill kind={ok ? 'ok' : 'danger'}>
                        {ok ? 'ok' : snapshot.scheduler.error || 'atenção'}
                      </Pill>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <EmptyState>Sem inventário Task Scheduler nos heartbeats recentes.</EmptyState>
        )}
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <h2 className="mb-3 font-semibold">Actividade recente</h2>
        <div className="space-y-2">
          {[
            ...heartbeats.slice(0, 8).map((item) => ({
              key: `hb-${item.source_id}-${item.seen_at}`,
              label: (
                <PipelineLabel
                  pipelineId={item.pipeline_id}
                  hostId={item.host_id || item.hostname}
                />
              ),
              meta: `${item.source_id || item.source_type || '--'} · ${formatDate(item.seen_at)} · ${item.status}`,
            })),
            ...triggers.slice(0, 5).map((item) => ({
              key: `tr-${item.trigger_id}`,
              label: (
                <PipelineLabel pipelineId={item.pipeline_id} hostId={item.host_id} />
              ),
              meta: `${item.trigger_id} · ${item.status}`,
            })),
          ].map((row) => (
            <div key={row.key} className="rounded-lg border border-slate-800 px-3 py-2">
              {row.label}
              <p className="font-mono text-xs text-slate-500">{row.meta}</p>
            </div>
          ))}
          {!heartbeats.length && !triggers.length && (
            <EmptyState>Ainda não há heartbeats ou triggers.</EmptyState>
          )}
        </div>
      </section>
    </AppShell>
  );
}
