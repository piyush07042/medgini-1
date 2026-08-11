import EmptyState from "./EmptyState";
import DashboardSkeleton from "./DashboardSkeleton";
import type { ActivityEvent } from "../../services/dashboardService";

export default function ActivityTimeline({
  data,
  loading,
}: {
  data: ActivityEvent[];
  loading: boolean;
}) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-soft sm:p-6">
      <div className="mb-5">
        <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-400">Activity Timeline</p>
        <h2 className="mt-2 text-xl font-semibold text-slate-900">Platform events</h2>
      </div>
      {loading ? (
        <DashboardSkeleton rows={5} />
      ) : data.length === 0 ? (
        <EmptyState
          title="No recent activity"
          description="Patient registrations, uploads, and predictions will show up here as you use the platform."
        />
      ) : (
        <div className="relative space-y-6 before:absolute before:inset-y-0 before:left-3 before:w-0.5 before:bg-slate-100">
          {data.map((event) => (
            <div key={event.id} className="group relative flex gap-6 pl-10 transition-all duration-300">
              {/* Timeline Dot */}
              <div className="absolute left-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-brand-100 ring-4 ring-white group-hover:scale-125 transition-transform duration-300">
                <div className="h-2 w-2 rounded-full bg-brand-500" />
              </div>
              <div className="flex-1 rounded-3xl border border-slate-100 bg-white p-5 shadow-sm transition-all duration-300 hover:border-brand-200 hover:shadow-md hover:bg-slate-50">
                <div className="flex flex-col gap-2 text-sm text-slate-500 sm:flex-row sm:items-center sm:justify-between">
                  <p className="font-semibold text-slate-900 group-hover:text-brand-900 transition-colors">{event.title}</p>
                  <span className="flex items-center gap-1.5 text-xs font-medium tracking-wide">
                    {event.time}
                  </span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-600">{event.description}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
