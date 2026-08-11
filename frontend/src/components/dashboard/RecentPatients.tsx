import { Users, FileDown } from "lucide-react";
import EmptyState from "./EmptyState";
import DashboardSkeleton from "./DashboardSkeleton";
import type { RecentPatient } from "../../services/dashboardService";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export default function RecentPatients({ data, loading }: { data: RecentPatient[]; loading: boolean }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-soft sm:p-6">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-400">Recent Patients</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">Patient activity</h2>
        </div>
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-3xl bg-brand-100 text-brand-700">
          <Users className="h-5 w-5" />
        </div>
      </div>
      {loading ? (
        <DashboardSkeleton rows={4} />
      ) : data.length === 0 ? (
        <EmptyState
          title="No patients yet"
          description="Add your first patient to start tracking visits, reports, and predictions."
          icon={<Users className="h-6 w-6" />}
        />
      ) : (
        <div className="space-y-4">
          <div className="hidden grid-cols-12 gap-4 text-xs uppercase tracking-[0.24em] text-slate-400 md:grid">
            <span className="col-span-4">Name</span>
            <span className="col-span-2">Age</span>
            <span className="col-span-3">Gender</span>
            <span className="col-span-3 text-right">PDF Report</span>
          </div>
          {data.map((patient) => (
            <div
              key={patient.id}
              className="rounded-3xl bg-slate-50 px-4 py-4 text-sm text-slate-700"
            >
              <div className="grid gap-2 md:grid-cols-12 md:gap-4 md:items-center">
                <div className="md:col-span-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-400 md:hidden">Name</p>
                  <p className="font-semibold text-slate-900">{patient.name}</p>
                </div>
                <div className="grid grid-cols-2 gap-3 md:col-span-8 md:grid-cols-8 md:items-center">
                  <div className="md:col-span-2">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-400 md:hidden">Age</p>
                    <p>{patient.age}</p>
                  </div>
                  <div className="md:col-span-3">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-400 md:hidden">Gender</p>
                    <p>{patient.gender}</p>
                  </div>
                  <div className="flex justify-end md:col-span-3">
                    <a
                      href={`${API_BASE_URL}/reports/medigenie/${patient.id}/pdf`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-2xl bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-brand-700 shadow-sm"
                    >
                      <FileDown className="h-3.5 w-3.5" />
                      Download PDF
                    </a>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

