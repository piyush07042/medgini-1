import InteractionSeverity from "./InteractionSeverity";
import type { DrugSafetyAssessmentResult } from "../../types/api";

export default function DrugRecommendation({ assessment }: { assessment: DrugSafetyAssessmentResult | null }) {
  if (!assessment) {
    return <p className="text-sm text-slate-500">Drug safety recommendations appear after a review is run.</p>;
  }

  const isHigh = assessment.overall_risk.toLowerCase().includes("high") || assessment.overall_risk.toLowerCase().includes("severe") || assessment.overall_risk.toLowerCase().includes("contraindicated");
  const isMod = assessment.overall_risk.toLowerCase().includes("moderate");
  const cardTone = isHigh ? "border-rose-200 bg-rose-50/30" : isMod ? "border-amber-200 bg-amber-50/30" : "border-emerald-200 bg-emerald-50/30";

  return (
    <div className={`rounded-3xl border p-6 shadow-sm ${cardTone}`}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">Clinical recommendation</p>
          <p className="mt-3 text-lg font-semibold text-slate-900">{assessment.overall_risk}</p>
        </div>
        <InteractionSeverity severity={assessment.overall_risk} />
      </div>
      <div className="mt-5 space-y-4">
        <div className="rounded-3xl border border-white/50 bg-white/70 p-5 shadow-sm backdrop-blur-sm">
          <p className="text-sm font-semibold text-slate-900">Summary</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{assessment.recommendation}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="rounded-3xl border border-white/50 bg-white/70 p-5 shadow-sm backdrop-blur-sm">
            <p className="text-sm font-semibold text-slate-900">Medications reviewed</p>
            <p className="mt-2 text-sm text-slate-700">{assessment.medications_checked.join(", ")}</p>
          </div>
          <div className="rounded-3xl border border-white/50 bg-white/70 p-5 shadow-sm backdrop-blur-sm">
            <p className="text-sm font-semibold text-slate-900">Patient conditions</p>
            <p className="mt-2 text-sm text-slate-700">{assessment.patient_conditions.join(", ") || "None captured"}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
