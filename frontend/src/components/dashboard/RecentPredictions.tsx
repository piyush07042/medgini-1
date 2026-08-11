import { Activity, FileDown } from "lucide-react";
import EmptyState from "./EmptyState";
import DashboardSkeleton from "./DashboardSkeleton";
import type { RecentPrediction } from "../../services/dashboardService";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const riskStyles: Record<string, string> = {
  Low: "bg-emerald-100 text-emerald-700",
  Moderate: "bg-amber-100 text-amber-700",
  High: "bg-rose-100 text-rose-700",
  Critical: "bg-red-200 text-red-800",
};

export default function RecentPredictions({ data, loading }: { data: RecentPrediction[]; loading: boolean }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-soft sm:p-6">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-400">Recent Predictions</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">Prediction history</h2>
        </div>
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-3xl bg-brand-100 text-brand-700">
          <Activity className="h-5 w-5" />
        </div>
      </div>
      {loading ? (
        <DashboardSkeleton rows={4} />
      ) : data.length === 0 ? (
        <EmptyState
          title="No predictions yet"
          description="Run a disease risk analysis from the prediction center to populate this feed."
          icon={<Activity className="h-6 w-6" />}
        />
      ) : (
        <div className="space-y-4">
          {data.map((item) => (
            <div key={item.id} className="rounded-3xl bg-slate-50 px-4 py-4 text-sm text-slate-700">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold text-slate-900">{item.patient}</p>
                  <p className="text-sm text-slate-500">{item.disease}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className={`rounded-full px-3 py-1 font-semibold ${riskStyles[item.risk] ?? "bg-slate-100 text-slate-700"}`}>
                    {item.risk}
                  </span>
                  <span className="rounded-full bg-white px-3 py-1 text-slate-500 ring-1 ring-slate-200">{item.confidence}</span>
                  <a
                    href={`${API_BASE_URL}/reports/medigenie/${item.id}/pdf`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 rounded-2xl bg-brand-600 px-2.5 py-1 text-xs font-semibold text-white transition hover:bg-brand-700 shadow-sm"
                  >
                    <FileDown className="h-3 w-3" />
                    PDF
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

