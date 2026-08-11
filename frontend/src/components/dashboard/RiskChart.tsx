import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import EmptyState from "./EmptyState";
import { ChartSkeleton } from "./DashboardSkeleton";
import type { BarSlice } from "../../services/dashboardService";

export default function RiskChart({ data, isLoading }: { data: BarSlice[]; isLoading: boolean }) {
  const hasData = data.some((slice) => slice.value > 0);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-soft sm:p-6">
      <div className="mb-5">
        <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-400">Risk Distribution</p>
        <h2 className="mt-2 text-xl font-semibold text-slate-900">Risk categories</h2>
      </div>
      {isLoading ? (
        <ChartSkeleton />
      ) : !hasData ? (
        <EmptyState title="No risk data yet" description="Risk distribution charts populate after AI clinical analyses are saved." />
      ) : (
        <div className="h-56 sm:h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="category" tickLine={false} axisLine={false} />
              <YAxis tickLine={false} axisLine={false} allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" radius={[12, 12, 0, 0]} fill="#7b95ff" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
