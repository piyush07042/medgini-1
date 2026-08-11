import { useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../../store/authStore";
import DashboardHeader from "../../components/dashboard/DashboardHeader";
import StatsCard from "../../components/dashboard/StatsCard";
import QuickActionCard from "../../components/dashboard/QuickActionCard";
import PredictionPieChart from "../../components/dashboard/PredictionPieChart";
import MonthlyTrendChart from "../../components/dashboard/MonthlyTrendChart";
import RiskChart from "../../components/dashboard/RiskChart";
import ReportsChart from "../../components/dashboard/ReportsChart";
import RecentPatients from "../../components/dashboard/RecentPatients";
import RecentReports from "../../components/dashboard/RecentReports";
import RecentPredictions from "../../components/dashboard/RecentPredictions";
import ActivityTimeline from "../../components/dashboard/ActivityTimeline";
import { DashboardHeaderSkeleton, StatsSkeleton } from "../../components/dashboard/DashboardSkeleton";
import toast from "react-hot-toast";
import { getDashboardData } from "../../services/dashboardService";

const actions = [
  { title: "Add Patient", subtitle: "New patient intake", to: "/patients" },
  { title: "Upload Report", subtitle: "Scan a new file", to: "/upload-report" },
  { title: "New Prediction", subtitle: "Run risk analysis", to: "/predictions" },
  { title: "AI Chat", subtitle: "Clinical assistant", to: "/chat" },
  { title: "Drug Safety", subtitle: "Medication review", to: "/drug-safety" },
  { title: "View Reports", subtitle: "Audit reports", to: "/reports" },
];

export default function DashboardPage() {
  const user = useAuthStore((state) => state.user);
  const dashboardQuery = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => getDashboardData(true),
    staleTime: 1000 * 60 * 2,
    retry: 1,
  });

  const greeting = useMemo(() => {
    if (!user) return "Welcome back";
    return `Welcome back, ${user.full_name ?? user.email}`;
  }, [user]);

  const currentDate = useMemo(
    () => new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" }),
    []
  );

  const summary = dashboardQuery.data?.summary.text ?? "Loading your workspace summary...";
  const isLoading = dashboardQuery.isLoading;
  const data = dashboardQuery.data;

  const queryClient = useQueryClient();

  // wire the refresh button in header
  const handleRefresh = async () => {
    try {
      // force fetch and invalidate cache
      await getDashboardData(true);
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      toast.success("Dashboard refreshed");
    } catch (e) {
      toast.error("Unable to refresh dashboard.");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 space-y-6 sm:space-y-8">
      {isLoading ? (
        <DashboardHeaderSkeleton />
      ) : (
        <DashboardHeader greeting={greeting} subtitle={`Current date: ${currentDate}`} summary={summary} onRefresh={handleRefresh} />
      )}

      <section className="grid gap-5 xl:grid-cols-[1.5fr_1fr]">
        <div className="space-y-5">
          {isLoading ? (
            <StatsSkeleton />
          ) : data?.stats.length ? (
            <div className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {data?.stats.map((stat) => (
                <StatsCard
                  key={stat.title}
                  title={stat.title}
                  value={stat.value}
                  trend={stat.trend}
                  label={stat.label}
                  positive={stat.positive}
                />
              ))}
            </div>
          ) : (
            <div className="rounded-3xl border border-dashed border-slate-200 bg-slate-50 p-6 text-sm text-slate-600">
              No dashboard metrics are available yet. Create a patient or run a prediction to populate the workspace.
            </div>
          )}

          <div className="grid gap-5 xl:grid-cols-2">
            <PredictionPieChart data={data?.prediction_distribution ?? []} isLoading={isLoading} />
            <MonthlyTrendChart data={data?.monthly_trends ?? []} isLoading={isLoading} />
          </div>

          <div className="grid gap-5 xl:grid-cols-2">
            <RiskChart data={data?.risk_distribution ?? []} isLoading={isLoading} />
            <ReportsChart data={data?.reports_area ?? []} isLoading={isLoading} />
          </div>
        </div>

        <div className="space-y-5">
          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-soft sm:p-5">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-400">Quick Actions</p>
                <h2 className="mt-2 text-xl font-semibold text-slate-900">Fast workflow access</h2>
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              {actions.map((action) => (
                <QuickActionCard key={action.title} title={action.title} subtitle={action.subtitle} to={action.to} />
              ))}
            </div>
          </div>

          <ActivityTimeline data={data?.activity ?? []} loading={isLoading} />
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.3fr_0.7fr]">
        <RecentPatients data={data?.recent_patients ?? []} loading={isLoading} />
        <div className="space-y-5">
          <RecentReports data={data?.recent_reports ?? []} loading={isLoading} />
          <RecentPredictions data={data?.recent_predictions ?? []} loading={isLoading} />
        </div>
      </section>

      {dashboardQuery.isError ? (
        <div className="rounded-3xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 sm:p-6">
          Unable to load live dashboard data. Check that the backend is running on port 8000 and try refreshing.
        </div>
      ) : null}
    </div>
  );
}
