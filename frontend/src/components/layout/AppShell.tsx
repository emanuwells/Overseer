import {
  Activity,
  GitBranch,
  LayoutDashboard,
  Menu,
  Server,
  X,
} from 'lucide-react';
import { useState, type ReactNode } from 'react';
import { Link, NavLink } from 'react-router-dom';
import type { DatabaseInfo } from '../../lib/types';
import { DbStatus } from '../ui/DbStatus';
import { Pill } from '../ui/Pill';

const NAV_ITEMS = [
  { id: 'operations', to: '/operations', label: 'Operações', hint: 'estado e KPIs', icon: LayoutDashboard },
  { id: 'runs', to: '/runs', label: 'Runs', hint: 'histórico e detalhe', icon: Activity },
  { id: 'dag', to: '/dag', label: 'DAG', hint: 'catálogo e módulos', icon: GitBranch },
  { id: 'environment', to: '/environment', label: 'Ambiente', hint: 'DB, hosts e actividade', icon: Server },
] as const;

export function AppShell({
  title,
  breadcrumb,
  actions,
  syncLabel,
  syncKind = '',
  database,
  onRefresh,
  children,
}: {
  title: string;
  breadcrumb?: string;
  actions?: ReactNode;
  syncLabel?: string;
  syncKind?: string;
  database?: DatabaseInfo;
  onRefresh?: () => void;
  children: ReactNode;
}) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[#0f1419] text-slate-100">
      <div className="flex min-h-screen">
        <aside
          className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-800 bg-[#121820] p-4 transition-transform lg:static lg:translate-x-0 ${
            mobileOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <div className="mb-4 flex items-center justify-between border-b border-slate-800 pb-4">
            <Link to="/operations" className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400 text-sm font-bold text-white">
                O
              </div>
              <div>
                <strong className="block text-sm">Overseer</strong>
                <span className="text-xs text-slate-400">observabilidade DAG</span>
              </div>
            </Link>
            <button
              type="button"
              className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 lg:hidden"
              onClick={() => setMobileOpen(false)}
              aria-label="Fechar menu"
            >
              <X size={18} />
            </button>
          </div>

          <nav className="flex flex-col gap-1" aria-label="Navegação principal">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.id}
                  to={item.to}
                  title={item.hint}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                      isActive
                        ? 'bg-blue-500/15 text-blue-200 ring-1 ring-blue-500/30'
                        : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                    }`
                  }
                >
                  <Icon size={18} className="shrink-0 opacity-80" />
                  <span className="flex flex-col">
                    <strong className="font-medium">{item.label}</strong>
                    <small className="text-xs text-slate-500">{item.hint}</small>
                  </span>
                </NavLink>
              );
            })}
          </nav>

          <DbStatus database={database} />
        </aside>

        {mobileOpen && (
          <button
            type="button"
            className="fixed inset-0 z-30 bg-black/50 lg:hidden"
            aria-label="Fechar menu"
            onClick={() => setMobileOpen(false)}
          />
        )}

        <main className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-20 flex flex-wrap items-center gap-3 border-b border-slate-800 bg-[#0f1419]/95 px-4 py-3 backdrop-blur">
            <button
              type="button"
              className="rounded-lg border border-slate-700 p-2 text-slate-300 hover:bg-slate-800 lg:hidden"
              onClick={() => setMobileOpen(true)}
              aria-label="Abrir menu"
            >
              <Menu size={18} />
            </button>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Link to="/operations" className="hover:text-slate-300">
                  Overseer
                </Link>
                <span>/</span>
                <span className="text-slate-300">{breadcrumb || title}</span>
              </div>
              <h1 className="mt-1 text-lg font-semibold tracking-tight">{title}</h1>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {actions}
              {syncLabel && <Pill kind={syncKind}>{syncLabel}</Pill>}
              {onRefresh && (
                <button
                  type="button"
                  onClick={onRefresh}
                  className="rounded-lg border border-slate-600 bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-500"
                >
                  Atualizar
                </button>
              )}
            </div>
          </header>
          <section className="flex-1 p-4 lg:p-6">{children}</section>
        </main>
      </div>
    </div>
  );
}
