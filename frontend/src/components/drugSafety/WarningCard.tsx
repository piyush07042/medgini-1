import InteractionSeverity from "./InteractionSeverity";

export default function WarningCard({
  title,
  details,
  recommendation,
  severity,
}: {
  title: string;
  details: string;
  recommendation: string;
  severity: string;
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          <p className="mt-2 text-sm text-slate-600">{details}</p>
        </div>
        <InteractionSeverity severity={severity} />
      </div>
      <div className="mt-4 rounded-3xl border border-slate-100 bg-slate-50 p-4">
        <p className="text-sm font-semibold text-slate-900">Recommended action</p>
        <p className="mt-2 text-sm leading-6 text-slate-700">{recommendation}</p>
      </div>
    </div>
  );
}
