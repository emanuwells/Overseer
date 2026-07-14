import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { DeploymentPicker } from '../components/layout/DeploymentPicker';
import { Alert, EmptyState } from '../components/ui/Alert';
import { Drawer } from '../components/ui/Drawer';
import { PipelineLabel } from '../components/ui/PipelineLabel';
import { Pill } from '../components/ui/Pill';
import { TokenBanner } from '../components/ui/TokenBanner';
import { api } from '../lib/api';
import type { DagEdge, DagNode, Pipeline, Run, RunModule } from '../lib/types';
import {
  computeBlockedDownstream,
  dedupePipelines,
  deploymentKey,
  isStaleRun,
  latestStatusByModule,
  orderNodesLinear,
  parseDeploymentKey,
  pipelineLabel,
  statusClass,
  statusLabel,
} from '../lib/utils';

export function DagPage() {
  const [params, setParams] = useSearchParams();
  const urlPipeline = params.get('pipeline') || '';
  const urlHost = params.get('host') || '';
  const [deploymentKeyState, setDeploymentKeyState] = useState(
    () => sessionStorage.getItem('overseer_selected_deployment') || '',
  );
  const [selectedNodeId, setSelectedNodeId] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (urlPipeline) setDeploymentKeyState(`${urlPipeline}::${urlHost}`);
  }, [urlPipeline, urlHost]);

  const query = useQuery({
    queryKey: ['dag', deploymentKeyState],
    queryFn: async () => {
      const pipelinesResponse = await api<{ items: Pipeline[] }>('/v1/read/pipelines');
      const pipelines = dedupePipelines(pipelinesResponse.items || []);
      let key = deploymentKeyState;
      if (!key && pipelines[0]) key = deploymentKey(pipelines[0]);
      const { pipelineId, hostId } = parseDeploymentKey(key);
      if (!pipelineId) return { pipelines, dag: null, modules: [] as RunModule[], lastRun: null as Run | null };

      const deployment = pipelines.find(
        (item) => item.pipeline_id === pipelineId && (item.host_id || '') === hostId,
      );
      const runsUrl = `/v1/read/runs?pipeline_id=${encodeURIComponent(pipelineId)}&host_id=${encodeURIComponent(hostId)}&limit=1`;
      const dagUrl = `/v1/read/pipelines/${encodeURIComponent(pipelineId)}/dag?host_id=${encodeURIComponent(hostId)}`;
      const [dagResponse, runsResponse] = await Promise.all([
        api<{ dag: { pipeline?: Pipeline; nodes?: DagNode[]; edges?: DagEdge[] } }>(dagUrl),
        api<{ items: Run[] }>(runsUrl),
      ]);
      const lastRun = runsResponse.items?.[0] || null;
      let modules: RunModule[] = [];
      if (lastRun?.run_id) {
        const detail = await api<{ modules?: RunModule[] }>(
          `/v1/read/runs/${encodeURIComponent(lastRun.run_id)}`,
        );
        modules = detail.modules || [];
      }
      return {
        pipelines,
        deployment,
        dag: dagResponse.dag,
        modules,
        lastRun,
        pipelineId,
        hostId,
      };
    },
  });

  const pipelines = query.data?.pipelines || [];
  const dag = query.data?.dag;
  const nodes = dag?.nodes || [];
  const edges = dag?.edges || [];
  const pipeline = dag?.pipeline;
  const deployment = query.data?.deployment;
  const modules = query.data?.modules || [];
  const lastRun = query.data?.lastRun;
  const pipelineId = query.data?.pipelineId || '';
  const hostId = query.data?.hostId || '';

  const latest = useMemo(() => latestStatusByModule(modules), [modules]);
  const blocked = useMemo(() => computeBlockedDownstream(edges, latest), [edges, latest]);
  const ordered = useMemo(() => orderNodesLinear(nodes, edges), [nodes, edges]);
  const selected = ordered.find((node) => node.module_id === selectedNodeId) || ordered[0];
  const hostLabel = deployment?.host_id || pipeline?.host_id || '--';
  const activeKey = deploymentKeyState || (pipelines[0] ? deploymentKey(pipelines[0]) : '');

  const onSelectDeployment = (key: string) => {
    setDeploymentKeyState(key);
    setSelectedNodeId('');
    setDrawerOpen(false);
    sessionStorage.setItem('overseer_selected_deployment', key);
    const { pipelineId: pid, hostId: hid } = parseDeploymentKey(key);
    const next = new URLSearchParams(params);
    next.set('pipeline', pid);
    if (hid) next.set('host', hid);
    else next.delete('host');
    setParams(next);
  };

  const openNode = (moduleId: string) => {
    setSelectedNodeId(moduleId);
    setDrawerOpen(true);
  };

  const nodeDetail = selected ? (
    <div className="space-y-4 text-sm">
      <div className="space-y-2">
        <div className="flex justify-between gap-2 border-b border-slate-800 py-2">
          <span className="text-slate-500">Módulo</span>
          <strong>{selected.label || selected.module_id}</strong>
        </div>
        <div className="flex justify-between gap-2 border-b border-slate-800 py-2">
          <span className="text-slate-500">Estado</span>
          <strong>
            {blocked.has(selected.module_id)
              ? 'blocked'
              : statusLabel(latest.get(selected.module_id)?.status || 'sem runtime')}
          </strong>
        </div>
        <div className="flex justify-between gap-2 border-b border-slate-800 py-2">
          <span className="text-slate-500">Comando</span>
          <strong className="max-w-[200px] truncate font-mono text-xs">
            {Array.isArray(selected.metadata?.command)
              ? (selected.metadata.command as string[]).join(' ')
              : String(selected.metadata?.command || '--')}
          </strong>
        </div>
      </div>
      {latest.get(selected.module_id)?.error_message && (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 p-2 text-xs text-rose-200">
          {latest.get(selected.module_id)?.error_message}
        </p>
      )}
      {lastRun?.run_id && (
        <Link
          to={`/runs?run=${encodeURIComponent(lastRun.run_id)}&pipeline=${encodeURIComponent(pipelineId)}&host=${encodeURIComponent(hostId)}`}
          className="inline-block rounded-lg border border-slate-600 px-3 py-1.5 text-xs hover:bg-slate-800"
        >
          Ver run {lastRun.run_id}
        </Link>
      )}
    </div>
  ) : null;

  return (
    <AppShell
      title={pipeline ? pipelineLabel(pipeline).title : 'Catálogo DAG'}
      breadcrumb={
        pipeline
          ? `DAG / ${pipelineLabel(pipeline).title} @ ${hostLabel}`
          : 'DAG / sem catálogo'
      }
      deploymentContext={
        pipelineId
          ? {
              pipelineId,
              hostId,
              label: pipeline ? pipelineLabel(pipeline).title : pipelineId,
            }
          : undefined
      }
      syncLabel={query.isFetching ? 'A carregar' : query.isError ? 'Erro' : pipeline ? 'Sincronizado' : 'Sem catálogo'}
      syncKind={query.isError ? 'danger' : pipeline ? 'ok' : 'warn'}
      onRefresh={() => query.refetch()}
      actions={
        <DeploymentPicker
          pipelines={pipelines}
          value={activeKey}
          onChange={onSelectDeployment}
          className="max-w-md"
        />
      }
    >
      <TokenBanner />
      {query.isError && <Alert message={(query.error as Error).message} />}
      <p className="mb-4 text-sm text-slate-400">
        {nodes.length} node(s), {edges.length} dependência(s).
        {lastRun ? ` Última run: ${lastRun.run_id}.` : ''} Clique num nó para inspeccionar.
      </p>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_300px]">
        <section className="relative min-h-[280px] overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/50 p-4">
          {ordered.length ? (
            <div className="relative" style={{ minWidth: ordered.length * 230 + 60, height: 240 }}>
              {ordered.slice(0, -1).map((node, index) => {
                const left = 30 + index * 230 + 180;
                const nextBlocked = blocked.has(ordered[index + 1].module_id);
                return (
                  <div
                    key={`edge-${node.module_id}`}
                    className={`absolute top-[168px] h-0.5 w-[70px] ${nextBlocked ? 'bg-rose-500/60' : 'bg-slate-600'}`}
                    style={{ left }}
                  />
                );
              })}
              {ordered.map((node, index) => {
                const left = 30 + index * 230;
                const runtime = latest.get(node.module_id);
                const isBlocked = blocked.has(node.module_id);
                const schedule = deployment?.schedule || pipeline?.schedule;
                const stale = isStaleRun(runtime?.started_at, runtime?.status, false, schedule);
                const klass = isBlocked ? 'blocked' : stale ? 'stale' : statusClass(runtime?.status);
                return (
                  <article
                    key={node.module_id}
                    onClick={() => openNode(node.module_id)}
                    className={`absolute w-[180px] cursor-pointer rounded-xl border p-3 transition-colors ${
                      selected?.module_id === node.module_id
                        ? 'border-blue-500/50 bg-blue-500/10'
                        : 'border-slate-700 bg-slate-900/80 hover:border-slate-500'
                    }`}
                    style={{ left, top: 120 }}
                  >
                    <span className="text-xs uppercase text-slate-500">{node.type || 'task'}</span>
                    <strong className="mt-1 block text-sm">{node.label || node.module_id}</strong>
                    <p className="font-mono text-xs text-slate-500">{node.module_id}</p>
                    <Pill kind={klass} className="mt-2">
                      {isBlocked ? 'blocked' : stale ? 'stale' : statusLabel(runtime?.status || 'sem runtime')}
                    </Pill>
                  </article>
                );
              })}
            </div>
          ) : (
            <EmptyState>Sem catálogo. Regista um DAG em /v1/catalog/pipelines.</EmptyState>
          )}
        </section>

        <aside className="hidden space-y-4 xl:block">
          {selected ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">{nodeDetail}</div>
          ) : pipeline ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-sm">
              <PipelineLabel source={pipeline} />
              <p className="mt-2 text-slate-400">Host: {hostLabel}</p>
              <p className="text-slate-400">Dono: {pipeline.owner}</p>
              <p className="text-slate-400">Agenda: {pipeline.schedule}</p>
            </div>
          ) : null}

          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
            <h3 className="mb-2 text-sm font-medium">Dependências</h3>
            {edges.length ? (
              <div className="space-y-2">
                {edges.map((edge) => (
                  <div
                    key={`${edge.from_module_id}-${edge.to_module_id}`}
                    className="flex items-center justify-between rounded-lg border border-slate-800 px-3 py-2 text-sm"
                  >
                    <div>
                      <strong>{edge.from_module_id}</strong>
                      <p className="text-xs text-slate-500">{edge.to_module_id}</p>
                    </div>
                    <Pill>edge</Pill>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState>Sem dependências registadas.</EmptyState>
            )}
          </div>
        </aside>
      </div>

      <Drawer
        open={drawerOpen}
        title={selected?.label || selected?.module_id || 'Módulo'}
        onClose={() => setDrawerOpen(false)}
      >
        {nodeDetail}
      </Drawer>
    </AppShell>
  );
}
