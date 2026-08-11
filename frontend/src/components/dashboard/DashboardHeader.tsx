import { ReactNode } from "react";
import { RefreshCw } from "lucide-react";

export default function DashboardHeader({
  greeting,
  subtitle,
  summary,
  children,
  onRefresh,
}: {
  greeting: string;
  subtitle: string;
  summary: string;
  children?: ReactNode;
  onRefresh?: () => void;
}) {
  return (
    <div className="grid gap-4 rounded-3xl border border-slate-200 bg-slate-50 p-5 shadow-soft sm:grid-cols-[1.5fr_1fr] sm:p-6 lg:p-8">
      <div>
        <p className="text-sm uppercase tracking-[0.24em] text-brand-600">Welcome</p>
        <h1 className="mt-3 text-2xl font-semibold text-slate-950 sm:text-4xl">{greeting}</h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">{subtitle}</p>
      </div>
      <div className="flex flex-col justify-center rounded-3xl bg-white p-5 shadow-sm ring-1 ring-slate-200 sm:p-6">
        <div className="mb-4 flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Today</p>
          <button id="dashboard-refresh" type="button" onClick={onRefresh} className="inline-flex items-center gap-2 rounded-full bg-white px-3 py-1.5 text-xs font-medium text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-50">
            <RefreshCw className="h-3.5 w-3.5 text-slate-600" />
            <span>Refresh</span>
          </button>
        </div>
        <div>
          <p className="text-lg font-semibold leading-snug text-slate-900 sm:text-xl">{summary}</p>
          <p className="mt-2 text-xs text-slate-500">Workspace summary — refresh to sync live data.</p>
        </div>
      </div>
      {children ? <div className="sm:col-span-2">{children}</div> : null}
    </div>
  );
}
