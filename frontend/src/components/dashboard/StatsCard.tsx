import { ArrowDown, ArrowUp } from "lucide-react";

export default function StatsCard({
  title,
  value,
  trend,
  label,
  positive,
}: {
  title: string;
  value: string;
  trend: string;
  label: string;
  positive: boolean;
}) {
  return (
    <div className="group relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-brand-500/10 hover:border-brand-200">
      <div className="absolute inset-0 bg-gradient-to-br from-white/50 to-white/0 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
      <div className="relative flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold tracking-wide text-slate-500">{title}</p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-slate-900 transition-colors group-hover:text-brand-900">{value}</p>
        </div>
        <div className={`inline-flex h-12 w-12 items-center justify-center rounded-2xl transition-transform duration-300 group-hover:scale-110 ${positive ? "bg-emerald-50 text-emerald-600 ring-4 ring-emerald-50/50" : "bg-rose-50 text-rose-600 ring-4 ring-rose-50/50"}`}>
          {positive ? <ArrowUp className="h-6 w-6" /> : <ArrowDown className="h-6 w-6" />}
        </div>
      </div>
      <div className="relative mt-4 flex items-center justify-between border-t border-slate-100 pt-4">
        <p className="text-xs font-medium text-slate-500">{label}</p>
        <p className={`rounded-full px-2.5 py-1 text-xs font-bold tracking-wide ${positive ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700"}`}>{trend}</p>
      </div>
    </div>
  );
}
