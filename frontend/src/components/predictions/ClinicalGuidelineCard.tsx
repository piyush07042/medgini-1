import { ShieldAlert, BookOpen, AlertTriangle, Clock } from "lucide-react";

interface GuidelineCitation {
  timeline?: string;
  action?: string;
  drug?: string;
  condition?: string;
}

interface ClinicalGuidelineCardProps {
  clinicalIntel?: {
    Guideline?: string;
    "Evidence Level"?: string;
    "Risk Interpretation"?: string;
    "Clinical Summary"?: string;
    "Recommended Next Steps"?: string[];
    "Lifestyle Advice"?: string[];
    "Monitoring Schedule"?: string[];
    guideline_citations?: string[];
    follow_up_plan?: Array<{ timeline: string; action: string }>;
    contraindications?: Array<{ drug: string; condition: string; action: string }>;
    emergency_signs?: string[];
  } | null;
}

export default function ClinicalGuidelineCard({ clinicalIntel }: ClinicalGuidelineCardProps) {
  if (!clinicalIntel || !clinicalIntel.Guideline) {
    return (
      <div className="rounded-3xl border border-slate-100 bg-slate-50/50 p-6 text-center">
        <ShieldAlert className="mx-auto h-8 w-8 text-slate-400" />
        <p className="mt-2 text-sm font-medium text-slate-600">No clinical guideline data matched for this case.</p>
      </div>
    );
  }

  const safeRender = (item: any): string => {
    if (typeof item === "object" && item !== null) {
      if (item.drug && item.condition && item.action) {
        return `Drug: ${item.drug} | If: ${item.condition} | Action: ${item.action}`;
      }
      return JSON.stringify(item);
    }
    return String(item);
  };

  const recommendations = clinicalIntel["Recommended Next Steps"] || [];
  const citations = clinicalIntel.guideline_citations || [];
  const followUp = clinicalIntel.follow_up_plan || [];
  const contraindications = clinicalIntel.contraindications || [];
  const emergency = clinicalIntel.emergency_signs || [];

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-base font-bold text-slate-900">Clinical Guidelines Integration</h4>
            <p className="text-xs text-slate-500">Evidence-based decision support panel</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700 ring-1 ring-indigo-200">
            {clinicalIntel.Guideline}
          </span>
          {clinicalIntel["Evidence Level"] && (
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
              Evidence {clinicalIntel["Evidence Level"]}
            </span>
          )}
        </div>
      </div>

      {/* Summary */}
      {clinicalIntel["Clinical Summary"] && (
        <div className="rounded-2xl bg-slate-50 p-4 border border-slate-100">
          <p className="text-sm font-semibold text-slate-900">Clinical Evaluation Summary</p>
          <p className="mt-1 text-sm text-slate-600 leading-relaxed">{clinicalIntel["Clinical Summary"]}</p>
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="space-y-3">
          <h5 className="text-sm font-bold text-slate-900">Guideline Recommendations</h5>
          <ul className="space-y-2">
            {recommendations.map((rec: any, i: number) => (
              <li key={i} className="flex items-start gap-3 rounded-2xl border border-slate-100 bg-white p-3 text-sm text-slate-700">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-indigo-50 text-xs font-bold text-indigo-600">
                  {i + 1}
                </span>
                <span>{safeRender(rec)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Follow-up Timeline */}
      {followUp.length > 0 && (
        <div className="space-y-3">
          <h5 className="text-sm font-bold text-slate-900">Monitoring & Follow-up Timeline</h5>
          <div className="relative border-l border-slate-200 pl-4 ml-2 space-y-4">
            {followUp.map((step, i) => (
              <div key={i} className="relative">
                <div className="absolute -left-[21px] top-1.5 flex h-2.5 w-2.5 items-center justify-center rounded-full bg-indigo-600 ring-4 ring-white" />
                <div className="flex items-baseline gap-2">
                  <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">{step.timeline}</span>
                </div>
                <p className="mt-0.5 text-sm text-slate-600">{step.action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contraindications & Warnings */}
      {contraindications.length > 0 && (
        <div className="space-y-3">
          <h5 className="text-sm font-bold text-rose-800 flex items-center gap-1.5">
            <AlertTriangle className="h-4 w-4" />
            Precautions & Contraindications
          </h5>
          <div className="grid gap-3 sm:grid-cols-2">
            {contraindications.map((item, i) => (
              <div key={i} className="rounded-2xl border border-rose-100 bg-rose-50/50 p-3 text-xs text-rose-900">
                <p className="font-bold uppercase tracking-wider">{item.drug}</p>
                <p className="mt-1 font-semibold text-rose-800">If: {item.condition}</p>
                <p className="mt-1 text-rose-700">{item.action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Emergency Signs */}
      {emergency.length > 0 && (
        <div className="rounded-2xl border border-amber-100 bg-amber-50/50 p-4">
          <h5 className="text-sm font-bold text-amber-800 flex items-center gap-1.5">
            <Clock className="h-4 w-4" />
            Red Flags & Emergency Signs
          </h5>
          <ul className="mt-2 space-y-1 list-disc list-inside text-xs text-amber-800">
            {emergency.map((sign: any, i: number) => (
              <li key={i} className="leading-relaxed">{safeRender(sign)}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Citations Footer */}
      {citations.length > 0 && (
        <div className="border-t border-slate-100 pt-4 text-[11px] text-slate-400">
          <p className="font-semibold uppercase tracking-wider text-slate-500 mb-1">Official References</p>
          <ul className="list-inside list-disc space-y-0.5">
            {citations.map((cite: any, i: number) => (
              <li key={i}>{safeRender(cite)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
