export default function AlternativeDrugCard({
  title,
  summary,
  items,
}: {
  title: string;
  summary: string;
  items: Array<{ label: string; note: string }>;
}) {
  return (
    <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
      <p className="text-sm font-semibold text-slate-900">{title}</p>
      <p className="mt-2 text-sm text-slate-600">{summary}</p>
      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div key={item.label} className="rounded-2xl border border-slate-200 bg-white p-4">
            <p className="font-semibold text-slate-900">{item.label}</p>
            <p className="mt-2 text-sm text-slate-700">{item.note}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
