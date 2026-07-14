import type { DatabaseInfo } from '../../lib/types';

export function DbStatus({ database }: { database?: DatabaseInfo }) {
  const reachable = Boolean(database?.reachable);
  const label = reachable ? `DB ${database?.mode || ''}` : 'DB indisponível';
  return (
    <div className="mt-auto rounded-xl border border-slate-700/80 bg-slate-900/50 p-3">
      <small className="block text-xs text-slate-400">{label}</small>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
        <span
          className={`block h-full transition-all ${reachable ? 'bg-emerald-400' : 'bg-rose-500'}`}
          style={{ width: reachable ? '100%' : '18%' }}
        />
      </div>
    </div>
  );
}

export function DbStatusMobile({ database }: { database?: DatabaseInfo }) {
  const reachable = Boolean(database?.reachable);
  const label = reachable ? `DB ${database?.mode || ''}` : 'DB indisponível';
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-mono lg:hidden ${
        reachable
          ? 'border-emerald-500/30 bg-emerald-500/15 text-emerald-300'
          : 'border-rose-500/30 bg-rose-500/15 text-rose-300'
      }`}
    >
      {label}
    </span>
  );
}
