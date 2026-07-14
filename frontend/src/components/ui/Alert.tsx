export function Alert({ message, type = 'error' }: { message: string; type?: string }) {
  const tone =
    type === 'error'
      ? 'border-rose-500/40 bg-rose-500/10 text-rose-100'
      : 'border-amber-500/40 bg-amber-500/10 text-amber-100';
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${tone}`} role="alert">
      {message}
    </div>
  );
}

export function EmptyState({ children }: { children: string }) {
  return (
    <div className="rounded-lg border border-dashed border-slate-600/60 px-4 py-8 text-center text-sm text-slate-400">
      {children}
    </div>
  );
}
