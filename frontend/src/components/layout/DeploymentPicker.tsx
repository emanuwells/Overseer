import { useMemo, useState } from 'react';
import { Search } from 'lucide-react';
import type { Pipeline } from '../../lib/types';
import { deploymentKey, pipelineLabel } from '../../lib/utils';

export function DeploymentPicker({
  pipelines,
  value,
  onChange,
  className = '',
}: {
  pipelines: Pipeline[];
  value: string;
  onChange: (deploymentKey: string) => void;
  className?: string;
}) {
  const [query, setQuery] = useState('');

  const options = useMemo(() => {
    const q = query.trim().toLowerCase();
    return pipelines
      .map((p) => {
        const key = deploymentKey(p);
        const label = pipelineLabel(p, '', '', pipelines);
        return { key, label, pipeline: p };
      })
      .filter((o) => {
        if (!q) return true;
        return (
          o.key.toLowerCase().includes(q) ||
          o.label.title.toLowerCase().includes(q) ||
          o.label.id.toLowerCase().includes(q)
        );
      });
  }, [pipelines, query]);

  return (
    <div className={`flex flex-col gap-2 sm:flex-row sm:items-center ${className}`}>
      <div className="relative min-w-[200px] flex-1">
        <Search size={16} className="pointer-events-none absolute left-2.5 top-2.5 text-slate-500" />
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filtrar deployment…"
          className="w-full rounded-lg border border-slate-700 bg-slate-900 py-2 pl-9 pr-3 text-sm"
        />
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="min-w-[220px] rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
      >
        <option value="">Seleccionar deployment…</option>
        {options.map((o) => (
          <option key={o.key} value={o.key}>
            {o.label.title} @ {o.pipeline.host_id || '—'}
          </option>
        ))}
      </select>
    </div>
  );
}
