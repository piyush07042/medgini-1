import { BarChart2, ShieldAlert } from "lucide-react";

export default function ExplainabilityPanel({ explanations }: { explanations?: Array<{ feature: string; importance: number }> | null }) {
  if (!explanations || explanations.length === 0) {
    return (
      <div className="rounded-3xl border border-slate-100 bg-slate-50/50 p-6 text-center">
        <ShieldAlert className="mx-auto h-8 w-8 text-slate-400" />
        <p className="mt-2 text-sm font-medium text-slate-600">Local explainability data is unavailable for this calculation.</p>
      </div>
    );
  }

  // Find max value to normalize widths
  const maxVal = Math.max(...explanations.map((e) => Math.abs(e.importance)), 0.001);

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
        <BarChart2 className="h-5 w-5 text-brand-600" />
        <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-500">Local Feature Contribution (SHAP / Coef)</h4>
      </div>

      <div className="space-y-4">
        {explanations.map((item, index) => {
          const rawVal = Math.abs(item.importance);
          const percent = Math.min(100, Math.round((rawVal / maxVal) * 100));

          return (
            <div key={index} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-slate-700 capitalize">{item.feature.replace(/_/g, " ")}</span>
                <span className="text-slate-500">{(rawVal).toFixed(3)}</span>
              </div>
              <div className="relative h-4 w-full overflow-hidden rounded-full bg-slate-100 ring-1 ring-inset ring-slate-200">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-brand-500 to-indigo-600 shadow-sm transition-all duration-1000 ease-out"
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
      <p className="text-[11px] leading-5 text-slate-500 italic">
        Contributions represent local SHAP values or model coefficients determining feature impact on this specific clinical prediction outcome.
      </p>
    </div>
  );
}
