import { Heart, Activity, AlertTriangle, Layers, TrendingUp, ShieldCheck, HeartPulse } from "lucide-react";

interface MultiDiseaseIntelligenceProps {
  data?: {
    combined_risk?: {
      organ_scores?: Record<string, number>;
      combined_risk_percent?: number;
      combined_risk_probability?: number;
      risk_category?: string;
    };
    health_index?: {
      health_score?: number;
      status?: string;
      description?: string;
    };
    comorbidities?: Array<{
      name: string;
      severity: string;
      criteria_met: string[];
      recommendation: string;
    }>;
    disease_interactions?: Array<{
      primary_disease: string;
      interacting_disease: string;
      effect: string;
      description: string;
      action: string;
    }>;
    longitudinal_timeline?: Array<{
      date: string;
      disease: string;
      risk_score_percent: number;
      risk_category: string;
      summary: string;
    }>;
  } | null;
}

export default function MultiDiseaseIntelligenceCard({ data }: MultiDiseaseIntelligenceProps) {
  if (!data || !data.combined_risk) {
    return (
      <div className="rounded-3xl border border-slate-100 bg-slate-50/50 p-6 text-center">
        <HeartPulse className="mx-auto h-8 w-8 text-slate-400" />
        <p className="mt-2 text-sm font-medium text-slate-600">No multi-disease intelligence data available for this profile.</p>
      </div>
    );
  }

  const combinedRisk = data.combined_risk;
  const healthIndex = data.health_index || { health_score: 80, status: "Optimal" };
  const comorbidities = data.comorbidities || [];
  const interactions = data.disease_interactions || [];
  const timeline = data.longitudinal_timeline || [];
  const organScores = combinedRisk.organ_scores || {};

  // Status color mapper
  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "optimal": return "bg-emerald-50 text-emerald-700 ring-emerald-200";
      case "fair": return "bg-sky-50 text-sky-700 ring-sky-200";
      case "guarded": return "bg-amber-50 text-amber-700 ring-amber-200";
      case "critical": return "bg-rose-50 text-rose-700 ring-rose-200";
      default: return "bg-slate-50 text-slate-700 ring-slate-200";
    }
  };

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
            <Layers className="h-5 w-5" />
          </div>
          <div>
            <h4 className="text-base font-bold text-slate-900">Multi-Disease Intelligence</h4>
            <p className="text-xs text-slate-500">Holistic patient health score & cross-organ risk profile</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`rounded-full px-3.5 py-1 text-xs font-bold ring-1 ${getStatusColor(healthIndex.status || "Optimal")}`}>
            Health Score: {healthIndex.health_score}/100 ({healthIndex.status})
          </span>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* Health Score Card */}
        <div className="rounded-2xl border border-slate-100 bg-gradient-to-br from-indigo-50/50 to-slate-50 p-4">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">MediGenie Health Index</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{healthIndex.health_score}</span>
            <span className="text-xs text-slate-500">/ 100</span>
          </div>
          <p className="mt-2 text-xs text-slate-600 leading-relaxed">{healthIndex.description}</p>
        </div>

        {/* Combined Risk Score */}
        <div className="rounded-2xl border border-slate-100 bg-gradient-to-br from-violet-50/50 to-slate-50 p-4">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Combined Multi-Organ Risk</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-slate-900">{combinedRisk.combined_risk_percent}%</span>
            <span className="text-xs font-semibold text-rose-600">({combinedRisk.risk_category})</span>
          </div>
          <p className="mt-2 text-xs text-slate-600">Unified risk probability across 6 key body systems.</p>
        </div>

        {/* Active Comorbidity Clusters */}
        <div className="rounded-2xl border border-slate-100 bg-gradient-to-br from-amber-50/50 to-slate-50 p-4 sm:col-span-2 lg:col-span-1">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Detected Syndromes</p>
          <p className="mt-2 text-2xl font-extrabold text-slate-900">{comorbidities.length}</p>
          <p className="mt-2 text-xs text-slate-600">Active comorbidity clusters & cross-disease risks.</p>
        </div>
      </div>

      {/* Organ System Risk Breakdown */}
      <div className="space-y-3">
        <h5 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Activity className="h-4 w-4 text-indigo-600" />
          Organ System Risk Breakdown
        </h5>
        <div className="grid gap-3 sm:grid-cols-2">
          {Object.entries(organScores).map(([organ, pct]) => (
            <div key={organ} className="space-y-1 rounded-2xl border border-slate-100 bg-slate-50/50 p-3 text-xs">
              <div className="flex items-center justify-between font-semibold">
                <span className="capitalize text-slate-700">{organ} System</span>
                <span className="text-slate-900 tabular-nums font-bold">{pct}%</span>
              </div>
              <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    pct >= 60 ? "bg-rose-500" : pct >= 35 ? "bg-amber-500" : "bg-emerald-500"
                  }`}
                  style={{ width: `${Math.min(100, Math.max(5, pct))}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Comorbidity Clusters */}
      {comorbidities.length > 0 && (
        <div className="space-y-3">
          <h5 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-500" />
            Detected Comorbidity Clusters
          </h5>
          <div className="space-y-3">
            {comorbidities.map((c, i) => (
              <div key={i} className="rounded-2xl border border-amber-200 bg-amber-50/40 p-4 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-900 text-sm">{c.name}</span>
                  <span className="rounded-full bg-amber-100 px-2.5 py-0.5 font-bold text-amber-800">
                    {c.severity} Severity
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {c.criteria_met.map((crit, idx) => (
                    <span key={idx} className="rounded-md bg-white/80 px-2 py-0.5 text-[11px] font-semibold text-slate-700 border border-amber-200/60">
                      ✓ {crit}
                    </span>
                  ))}
                </div>
                <p className="text-slate-700 pt-1 border-t border-amber-200/40">{c.recommendation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Disease Interactions */}
      {interactions.length > 0 && (
        <div className="space-y-3">
          <h5 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Heart className="h-4 w-4 text-rose-500" />
            Cross-Disease Interaction Analysis
          </h5>
          <div className="grid gap-3 sm:grid-cols-2">
            {interactions.map((item, i) => (
              <div key={i} className="rounded-2xl border border-slate-200 bg-white p-4 space-y-1.5 text-xs shadow-sm">
                <p className="font-bold text-indigo-700">
                  {item.primary_disease} ↔ {item.interacting_disease}
                </p>
                <p className="font-semibold text-slate-900">{item.effect}</p>
                <p className="text-slate-600 leading-relaxed">{item.description}</p>
                <p className="text-slate-800 font-semibold pt-1 border-t border-slate-100">Action: {item.action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Longitudinal Risk Timeline */}
      {timeline.length > 0 && (
        <div className="space-y-3">
          <h5 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-indigo-600" />
            Longitudinal Patient History & Risk Timeline
          </h5>
          <div className="relative border-l border-slate-200 pl-4 ml-2 space-y-4">
            {timeline.map((item, i) => (
              <div key={i} className="relative">
                <div className="absolute -left-[21px] top-1.5 flex h-2.5 w-2.5 items-center justify-center rounded-full bg-indigo-600 ring-4 ring-white" />
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-900">{item.disease}</span>
                  <span className="text-slate-400">{item.date}</span>
                </div>
                <div className="mt-1 flex items-center gap-2 text-xs">
                  <span className="font-semibold text-indigo-600">{item.risk_score_percent}% Risk</span>
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600">{item.risk_category}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
