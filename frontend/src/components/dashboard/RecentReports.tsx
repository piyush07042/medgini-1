import { FileText, FileDown } from "lucide-react";
import EmptyState from "./EmptyState";
import DashboardSkeleton from "./DashboardSkeleton";
import type { RecentReport } from "../../services/dashboardService";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const statusStyles: Record<string, string> = {
  Completed: "bg-emerald-100 text-emerald-700",
  Pending: "bg-amber-100 text-amber-700",
  Review: "bg-sky-100 text-sky-700",
};

export default function RecentReports({ data, loading }: { data: RecentReport[]; loading: boolean }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-4 shadow-soft sm:p-6">
      <div className="mb-5 flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.28em] text-slate-400">Recent Reports</p>
          <h2 className="mt-2 text-xl font-semibold text-slate-900">Latest uploads</h2>
        </div>
        <div className="inline-flex h-12 w-12 items-center justify-center rounded-3xl bg-brand-100 text-brand-700">
          <FileText className="h-5 w-5" />
        </div>
      </div>
      {loading ? (
        <DashboardSkeleton rows={3} />
      ) : data.length === 0 ? (
        <EmptyState
          title="No reports uploaded"
          description="Upload a medical report to run OCR and generate AI clinical summaries."
          icon={<FileText className="h-6 w-6" />}
        />
      ) : (
        <div className="space-y-4">
          {data.map((report) => (
            <div key={report.id} className="rounded-3xl bg-slate-50 px-4 py-4 text-sm text-slate-700">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="break-all font-semibold text-slate-900">{report.filename}</p>
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] ${
                      statusStyles[report.status] ?? "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {report.status}
                  </span>
                  <a
                    href={`${API_BASE_URL}/reports/medigenie/${report.id}/pdf`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 rounded-2xl bg-brand-600 px-2.5 py-1 text-xs font-semibold text-white transition hover:bg-brand-700 shadow-sm"
                  >
                    <FileDown className="h-3 w-3" />
                    PDF
                  </a>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-4 text-xs text-slate-500">
                <span>{report.uploadedAt}</span>
                <span>Report ID #{report.id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

