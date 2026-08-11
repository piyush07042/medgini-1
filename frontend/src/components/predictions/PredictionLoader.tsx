export default function PredictionLoader() {
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
      <div className="animate-pulse space-y-4">
        <div className="h-6 w-32 rounded-full bg-slate-200" />
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="h-24 rounded-3xl bg-slate-100" />
          <div className="h-24 rounded-3xl bg-slate-100" />
        </div>
        <div className="h-12 rounded-3xl bg-slate-100" />
        <div className="h-40 rounded-3xl bg-slate-100" />
      </div>
    </div>
  );
}
