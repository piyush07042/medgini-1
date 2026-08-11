import { Clock3 } from "lucide-react";
import type { DrugSafetyStoredAssessment } from "../../types/api";

export default function DrugHistory({ history }: { history: DrugSafetyStoredAssessment[] }) {
  return (
    <div className="space-y-4">
      {history.map((item) => (
        <div key={item.id} className="rounded-3xl border border-slate-200 bg-white p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="font-semibold text-slate-900">Assessment #{item.id}</p>
              <p className="text-sm text-slate-500">{new Date(item.created_at).toLocaleString()}</p>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-slate-700">
              <Clock3 className="h-3.5 w-3.5" />
              Stored
            </div>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-700">{item.assessment.drug_safety_assessment?.recommendation || "No summary available."}</p>
        </div>
      ))}
    </div>
  );
}
