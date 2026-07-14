import { hasApiToken } from '../../lib/config';

export function TokenBanner() {
  if (hasApiToken()) return null;
  return (
    <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
      Para aceder à API em produção, configure o token em{' '}
      <code className="rounded bg-black/30 px-1.5 py-0.5 font-mono text-xs">overseer-config.js</code>.
    </div>
  );
}
