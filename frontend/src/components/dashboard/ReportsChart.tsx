import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import EmptyState from "./EmptyState";
import { ChartSkeleton } from "./DashboardSkeleton";
import type { AreaData } from "../../services/dashboardService";

export default function ReportsChart({ data, isLoading }: { data: AreaData[]; isLoading: boolean }) {
  const hasData = data.some((point) => point.generated > 0);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-soft sm:p-6">
      <div className="mb-5">
        <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-400">Reports Generated</p>
        <h2 className="mt-2 text-xl font-semibold text-slate-900">Document output</h2>
      </div>
      {isLoading ? (
        <ChartSkeleton />
      ) : !hasData ? (
        <EmptyState title="No generated reports yet" description="Uploaded and AI-generated reports will chart here over time." />
      ) : (
        <div className="h-56 sm:h-72">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="reportsGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#4f6dff" stopOpacity={0.75} />
                  <stop offset="95%" stopColor="#4f6dff" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="month" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip />
              <Area type="monotone" dataKey="generated" stroke="#4f6dff" fill="url(#reportsGradient)" strokeWidth={3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
