export default function DashboardSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-3">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-14 rounded-3xl bg-slate-100" />
      ))}
    </div>
  );
}

export function ChartSkeleton() {
  return <div className="h-56 animate-pulse rounded-3xl bg-slate-100 sm:h-72" />;
}

export function StatsSkeleton() {
  return (
    <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="h-36 animate-pulse rounded-3xl bg-slate-100" />
      ))}
    </div>
  );
}

export function DashboardHeaderSkeleton() {
  return (
    <div className="grid gap-4 rounded-3xl border border-slate-200 bg-slate-50 p-5 shadow-soft sm:grid-cols-[1.5fr_1fr] sm:p-6 lg:p-8">
      <div className="space-y-3">
        <div className="h-3 w-24 animate-pulse rounded-full bg-slate-200" />
        <div className="h-8 w-3/4 animate-pulse rounded-full bg-slate-200" />
        <div className="h-4 w-full animate-pulse rounded-full bg-slate-200" />
        <div className="h-4 w-2/3 animate-pulse rounded-full bg-slate-200" />
      </div>
      <div className="h-32 animate-pulse rounded-3xl bg-slate-200" />
    </div>
  );
}
