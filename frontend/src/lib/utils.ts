import type { DagEdge, DagNode, Pipeline, Run, RunModule } from './types';

export function statusClass(status?: string): string {
  const raw = String(status || '').toLowerCase();
  if (['ok', 'success', 'done', 'completed', 'ready'].includes(raw)) return 'ok';
  if (['warning', 'warn', 'queued', 'running', 'claimed', 'late'].includes(raw)) return 'warn';
  if (!raw) return '';
  return 'danger';
}

export function stateBucket(status?: string): string {
  const klass = statusClass(status);
  if (klass === 'ok') return 'ok';
  if (klass === 'warn') return 'warn';
  if (klass === 'danger') return 'danger';
  return 'all';
}

export function statusLabel(status?: string): string {
  return status || 'sem estado';
}

export function formatDate(value?: string | null): string {
  if (!value) return '--';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString('pt-PT', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function duration(value?: number | string | null): string {
  if (value === null || value === undefined || value === '') return '--';
  const seconds = Number(value);
  if (!Number.isFinite(seconds)) return String(value);
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

export function logicalPipelineId(pipelineId?: string): string {
  const raw = String(pipelineId || '');
  const idx = raw.lastIndexOf('__');
  if (idx > 0) {
    const host = raw.slice(idx + 2);
    if (host) return raw.slice(0, idx);
  }
  return raw;
}

export function effectiveHostId(item?: {
  host_id?: string;
  pipeline_id?: string;
  metadata?: Record<string, unknown>;
} | null): string {
  if (!item) return '';
  const explicit = String(item.host_id || '').trim();
  if (explicit && explicit.toLowerCase() !== 'any') return explicit;
  const metaHost = String(item.metadata?.host_id || '').trim();
  if (metaHost) return metaHost;
  const legacy = String(item.pipeline_id || '').includes('__')
    ? String(item.pipeline_id).split('__').pop() || ''
    : '';
  return legacy;
}

export function hostKeyMatch(left?: string, right?: string): boolean {
  return String(left || '').trim().toUpperCase() === String(right || '').trim().toUpperCase();
}

export function normalizePipelineRow(item?: Pipeline | null): Pipeline | null {
  if (!item) return null;
  const logicalId = logicalPipelineId(item.pipeline_id);
  if (!logicalId) return null;
  const candidate = { ...item, pipeline_id: logicalId };
  const host = effectiveHostId(candidate);
  if (host) candidate.host_id = host;
  return candidate;
}

export function dedupePipelines(pipelines?: Pipeline[]): Pipeline[] {
  return (pipelines || [])
    .map((item) => normalizePipelineRow(item))
    .filter((item): item is Pipeline => Boolean(item && effectiveHostId(item)))
    .sort((left, right) => {
      const byPipeline = String(left.pipeline_id).localeCompare(String(right.pipeline_id));
      if (byPipeline !== 0) return byPipeline;
      return String(left.host_id || '').localeCompare(String(right.host_id || ''));
    });
}

export function deploymentKey(item: Pipeline | string, hostId = ''): string {
  const logicalId = typeof item === 'string' ? logicalPipelineId(item) : logicalPipelineId(item.pipeline_id);
  const host = typeof item === 'object' ? (item.host_id || '') : hostId;
  return `${logicalId}::${host}`;
}

export function runDeploymentKey(run: Run): string {
  return deploymentKey(run.pipeline_id, run.host_id || '');
}

export function parseDeploymentKey(key: string): { pipelineId: string; hostId: string } {
  const [pipelineId, hostId = ''] = String(key || '').split('::');
  return { pipelineId, hostId };
}

export function findPipelineRow(
  pipelines: Pipeline[],
  pipelineId: string,
  hostId: string,
): Pipeline | null {
  const logicalId = logicalPipelineId(pipelineId);
  const hostKey = String(hostId || '').trim();
  return (
    pipelines.find(
      (item) =>
        logicalPipelineId(item.pipeline_id) === logicalId &&
        hostKeyMatch(effectiveHostId(item), hostKey),
    ) || null
  );
}

export function pipelineLabel(
  source?: Pipeline | Run | null,
  pipelineId = '',
  hostId = '',
  pipelines: Pipeline[] = [],
): { title: string; subtitle: string; id: string } {
  const row =
    typeof source === 'object' && source
      ? source
      : findPipelineRow(pipelines, pipelineId, hostId);
  const id = logicalPipelineId(
    (source as Pipeline)?.pipeline_id || pipelineId || row?.pipeline_id || '',
  );
  const title =
    (source as Pipeline)?.pipeline_name ||
    (source as Pipeline)?.name ||
    row?.pipeline_name ||
    row?.name ||
    id ||
    '--';
  const subtitle = id && id !== title ? id : '';
  return { title, subtitle, id };
}

export function pipelineDisplayName(item: Pipeline): string {
  return pipelineLabel(item).title;
}

export function hostDisplay(item: Pipeline): string {
  const host = effectiveHostId(item);
  return host || '--';
}

export function criticalityClass(value?: string): string {
  const raw = String(value || '').toLowerCase();
  if (raw === 'critical' || raw === 'high') return 'danger';
  if (raw === 'low') return 'ok';
  return 'warn';
}

export function isManualSchedule(schedule?: string | null): boolean {
  const normalized = String(schedule || 'manual').trim().toLowerCase();
  return !normalized || normalized === 'manual' || normalized === 'paused';
}

export function isStaleRun(
  startedAt?: string,
  status?: string,
  deploymentStale = false,
  schedule?: string | null,
): boolean {
  if (isManualSchedule(schedule)) return false;
  if (deploymentStale) return true;
  if (String(status || '').toLowerCase() !== 'running' || !startedAt) return false;
  const date = new Date(startedAt);
  if (Number.isNaN(date.getTime())) return false;
  return Date.now() - date.getTime() > 24 * 60 * 60 * 1000;
}

export function deploymentStaleFlag(item?: Pipeline | null): boolean {
  if (isManualSchedule(item?.schedule)) return false;
  return Boolean(item?.is_stale);
}

export function deploymentShowsStale(item?: Pipeline | null): boolean {
  if (!item || isManualSchedule(item.schedule)) return false;
  return (
    deploymentStaleFlag(item) ||
    isStaleRun(item.last_started_at, item.last_status, false, item.schedule)
  );
}

export function latestStatusByModule(modules: RunModule[]): Map<string, RunModule> {
  const latest = new Map<string, RunModule>();
  modules.forEach((item) => {
    if (!latest.has(item.module_id)) latest.set(item.module_id, item);
  });
  return latest;
}

export function orderNodesLinear(nodes: DagNode[], edges: DagEdge[]): DagNode[] {
  if (!nodes.length) return [];
  const byId = new Map(nodes.map((node) => [node.module_id, node]));
  const targets = new Set(edges.map((edge) => edge.to_module_id));
  let current =
    nodes.find((node) => !targets.has(node.module_id))?.module_id || nodes[0].module_id;
  const ordered: DagNode[] = [];
  const seen = new Set<string>();
  while (current && !seen.has(current)) {
    seen.add(current);
    if (byId.has(current)) ordered.push(byId.get(current)!);
    current = edges.find((edge) => edge.from_module_id === current)?.to_module_id || '';
  }
  nodes.forEach((node) => {
    if (!seen.has(node.module_id)) ordered.push(node);
  });
  return ordered;
}

export function computeBlockedDownstream(
  edges: DagEdge[],
  latest: Map<string, RunModule>,
): Set<string> {
  const failed = new Set<string>();
  latest.forEach((item, moduleId) => {
    if (statusClass(item.status) === 'danger') failed.add(moduleId);
  });
  const adj = new Map<string, string[]>();
  edges.forEach((edge) => {
    if (!adj.has(edge.from_module_id)) adj.set(edge.from_module_id, []);
    adj.get(edge.from_module_id)!.push(edge.to_module_id);
  });
  const blocked = new Set<string>();
  const queue = [...failed];
  while (queue.length) {
    const id = queue.shift()!;
    for (const next of adj.get(id) || []) {
      if (!blocked.has(next) && !failed.has(next)) {
        blocked.add(next);
        queue.push(next);
      }
    }
  }
  return blocked;
}

export async function copyText(value: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    return false;
  }
}
