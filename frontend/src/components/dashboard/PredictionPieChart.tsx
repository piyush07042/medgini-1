import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from "recharts";
import EmptyState from "./EmptyState";
import { ChartSkeleton } from "./DashboardSkeleton";
import type { PieSlice } from "../../services/dashboardService";

const COLORS = ["#4f6dff", "#7b95ff", "#4ade80", "#f59e0b", "#fb7185", "#10b981", "#6366f1", "#0ea5e9", "#8b5cf6"];

export default function PredictionPieChart({ data, isLoading }: { data: PieSlice[]; isLoading: boolean }) {
  const hasData = data.some((slice) => slice.value > 0);

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-soft sm:p-6">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-400">Disease Prediction Distribution</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">Prediction mix</h2>
        </div>
      </div>
      {isLoading ? (
        <ChartSkeleton />
      ) : !hasData ? (
        <EmptyState
          title="No prediction data"
          description="Prediction distribution will appear after you run clinical analyses or disease models."
        />
      ) : (
        <div className="h-56 sm:h-72">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius="70%" fill="#8884d8" label>
                {data.map((entry, index) => (
                  <Cell key={`cell-${entry.name}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => `${value} runs`} />
              <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
