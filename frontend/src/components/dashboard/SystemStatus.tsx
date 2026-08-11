import type { ReactNode } from "react";
import { CircleDot, ShieldCheck, ServerCog, Database, Sparkles, KeyRound, BookOpen } from "lucide-react";
import type { SystemStatusItem } from "../../services/dashboardService";

const statusStyles: Record<string, string> = {
  Online: "bg-emerald-100 text-emerald-700",
  Degraded: "bg-amber-100 text-amber-700",
  Offline: "bg-rose-100 text-rose-700",
};

const iconMap: Record<string, ReactNode> = {
  "Backend API": <ServerCog className="h-4 w-4" />,
  Database: <Database className="h-4 w-4" />,
  "OCR Service": <CircleDot className="h-4 w-4" />,
  "AI Models Loaded": <Sparkles className="h-4 w-4" />,
  "Knowledge Base": <BookOpen className="h-4 w-4" />,
  Authentication: <KeyRound className="h-4 w-4" />,
};

export default function SystemStatus({ data, loading }: { data: SystemStatusItem[]; loading: boolean }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-soft sm:p-6">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-400">System Health</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">Operational status</h2>
        </div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        {loading
          ? Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-24 animate-pulse rounded-3xl bg-slate-100" />
            ))
          : data.map((item) => (
              <div key={item.service} className="group flex flex-col gap-3 rounded-3xl bg-slate-50 p-4 transition-all duration-300 hover:bg-slate-100 hover:shadow-sm">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-white text-brand-600 shadow-sm transition-transform duration-300 group-hover:scale-110">
                      {iconMap[item.service] ?? <ShieldCheck className="h-4 w-4" />}
                    </div>
                    <p className="text-sm font-semibold text-slate-900">{item.service}</p>
                  </div>
                  <span className={`shrink-0 flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider ${statusStyles[item.status] ?? "bg-slate-100 text-slate-700"}`}>
                    {item.status === "Online" && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />}
                    {item.status}
                  </span>
                </div>
                <p className="text-sm text-slate-500">{item.description}</p>
              </div>
            ))}
      </div>
    </section>
  );
}
