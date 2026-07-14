import type { ReactNode } from 'react';

const styles: Record<string, string> = {
  ok: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  warn: 'bg-amber-500/15 text-amber-200 border-amber-500/30',
  danger: 'bg-rose-500/15 text-rose-300 border-rose-500/30',
  stale: 'bg-orange-500/15 text-orange-200 border-orange-500/30',
  '': 'bg-slate-500/15 text-slate-300 border-slate-500/30',
};

export function Pill({
  kind = '',
  children,
  className = '',
}: {
  kind?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium font-mono tabular-nums ${styles[kind] || styles['']} ${className}`}
    >
      {children}
    </span>
  );
}
