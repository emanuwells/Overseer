import type { Pipeline, Run } from '../../lib/types';
import { effectiveHostId, pipelineLabel } from '../../lib/utils';

export function PipelineLabel({
  source,
  pipelineId = '',
  hostId = '',
  pipelines = [],
}: {
  source?: Pipeline | Run | Record<string, unknown> | null;
  pipelineId?: string;
  hostId?: string;
  pipelines?: Pipeline[];
}) {
  const label = pipelineLabel(
    source as Pipeline | Run | null,
    pipelineId,
    hostId,
    pipelines,
  );
  const host = hostId || (source ? effectiveHostId(source as Pipeline) : '');
  const hostSuffix = host ? ` @ ${host}` : '';
  return (
    <span className="inline-flex flex-col gap-0.5">
      <strong className="text-slate-100">{label.title}</strong>
      {(label.subtitle || host) && (
        <span className="font-mono text-xs text-slate-400">
          {label.subtitle}
          {hostSuffix}
        </span>
      )}
    </span>
  );
}
