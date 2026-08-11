import { useEffect, useState } from "react";
import { BrainCircuit, BarChart2, RefreshCw, ChevronDown, ChevronUp, FlaskConical } from "lucide-react";
import PageHeading from "../../components/PageHeading";
import Card from "../../components/Card";

const API_BASE = "/api/v1/evaluation";

const DISEASES = [
  "heart_disease", "diabetes", "kidney_disease", "liver_disease",
  "breast_cancer", "parkinsons", "hepatitis", "heart_failure", "stroke",
];

interface XaiFeature {
  feature: string;
  importance: number;
}

interface XaiModel {
  disease_key: string;
  disease_name: string;
  has_shap_plot: boolean;
  has_feature_importance_plot: boolean;
  top_features: XaiFeature[];
  metrics: {
    accuracy?: number;
    f1_score?: number;
    roc_auc?: number;
    precision?: number;
    recall?: number;
  };
}

function FeatureBar({ feature, importance, max }: { feature: string; importance: number; max: number }) {
  const pct = Math.min(100, Math.round((importance / Math.max(max, 0.001)) * 100));
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium text-slate-700 capitalize">{feature.replace(/_/g, " ")}</span>
        <span className="text-slate-500 tabular-nums">{importance.toFixed(4)}</span>
      </div>
      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100 ring-1 ring-inset ring-slate-200">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-600 transition-all duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function ModelXaiCard({ model }: { model: XaiModel }) {
  const [expanded, setExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState<"features" | "shap" | "importance">("features");
  const maxImportance = Math.max(...(model.top_features?.map((f) => f.importance) ?? [0.001]), 0.001);

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft transition-shadow hover:shadow-md">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600">
            <FlaskConical className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-900">{model.disease_name}</p>
            <p className="text-xs text-slate-500">{model.top_features?.length ?? 0} feature contributions computed</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {model.metrics?.roc_auc != null && (
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 ring-1 ring-emerald-200">
              AUC {(model.metrics.roc_auc * 100).toFixed(1)}%
            </span>
          )}
          <button
            onClick={() => setExpanded((e) => !e)}
            aria-label={expanded ? "Collapse" : "Expand"}
            className="flex h-8 w-8 items-center justify-center rounded-xl bg-slate-100 text-slate-500 hover:bg-slate-200 transition"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="px-5 pb-5 pt-4">
          {/* Tabs */}
          <div className="mb-4 flex gap-2">
            {(["features", "shap", "importance"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                  activeTab === tab
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {tab === "features" ? "Feature Contributions" : tab === "shap" ? "SHAP Plot" : "Importance Plot"}
              </button>
            ))}
          </div>

          {activeTab === "features" && (
            <div className="space-y-3">
              {model.top_features?.length ? (
                model.top_features.map((f, i) => (
                  <FeatureBar key={i} feature={f.feature} importance={f.importance} max={maxImportance} />
                ))
              ) : (
                <p className="text-sm text-slate-500 italic">No SHAP values computed for this model yet.</p>
              )}
              <p className="mt-3 text-[11px] italic text-slate-400">
                Values represent global mean absolute SHAP values across the test set, indicating average feature impact on model output.
              </p>
            </div>
          )}

          {activeTab === "shap" && (
            <div>
              {model.has_shap_plot ? (
                <img
                  src={`${API_BASE}/plot/${model.disease_key}/shap_summary.png`}
                  alt={`SHAP Summary - ${model.disease_name}`}
                  className="w-full rounded-2xl border border-slate-200 shadow-sm"
                />
              ) : (
                <p className="text-sm text-slate-500 italic">SHAP summary plot not available for this model.</p>
              )}
            </div>
          )}

          {activeTab === "importance" && (
            <div>
              {model.has_feature_importance_plot ? (
                <img
                  src={`${API_BASE}/plot/${model.disease_key}/feature_importance.png`}
                  alt={`Feature Importance - ${model.disease_name}`}
                  className="w-full rounded-2xl border border-slate-200 shadow-sm"
                />
              ) : (
                <p className="text-sm text-slate-500 italic">Feature importance plot not available.</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function XaiDashboardPage() {
  const [data, setData] = useState<{ models: XaiModel[]; total_models: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/xai/global`);
      if (!res.ok) throw new Error("Failed to load XAI global explanation data.");
      const json = await res.json();
      setData(json);
    } catch (e: any) {
      setError(e.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <PageHeading
          title="Explainable AI Dashboard"
          description="Global SHAP-based explanations, local feature contributions, and model interpretability for all 9 disease classifiers."
        />
        <button
          onClick={fetchData}
          className="inline-flex items-center gap-2 rounded-2xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh Explanations
        </button>
      </div>

      {/* Hero Banner */}
      <div className="flex flex-col gap-6 rounded-3xl bg-gradient-to-r from-indigo-950 via-violet-950 to-slate-900 p-7 text-white shadow-xl md:flex-row md:items-center">
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white/10 text-indigo-300 ring-1 ring-white/10">
          <BrainCircuit className="h-9 w-9" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-white">Global & Local Explainability</h2>
          <p className="mt-1 max-w-3xl text-sm text-indigo-200">
            MediGenie integrates SHAP (SHapley Additive exPlanations) to provide clinically meaningful interpretability for every prediction. 
            This dashboard shows which clinical features are driving the AI decisions, both globally across the training dataset 
            and locally for each patient prediction.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {["SHAP Values", "Feature Importance", "Global Explanations", "Local Contributions", "Model Interpretability"].map((tag) => (
              <span key={tag} className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-indigo-200 ring-1 ring-white/20">
                {tag}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Stats Strip */}
      {data && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: "Total Models", value: data.total_models },
            { label: "SHAP Enabled", value: data.models.filter((m) => m.has_shap_plot).length },
            { label: "Feature Importance Plots", value: data.models.filter((m) => m.has_feature_importance_plot).length },
            { label: "Avg Features/Model", value: Math.round(data.models.reduce((a, m) => a + (m.top_features?.length ?? 0), 0) / (data.total_models || 1)) },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-3xl border border-slate-200 bg-white p-5 text-center shadow-soft">
              <p className="text-3xl font-bold text-slate-900">{value}</p>
              <p className="mt-1 text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Model Cards */}
      <div>
        <div className="mb-4 flex items-center gap-2 border-b border-slate-200 pb-3">
          <BarChart2 className="h-5 w-5 text-indigo-600" />
          <h2 className="text-lg font-bold text-slate-900">Per-Model Feature Explanations</h2>
          <span className="ml-auto rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
            Click any card to expand SHAP & feature charts
          </span>
        </div>

        {loading && (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 9 }).map((_, i) => (
              <div key={i} className="h-20 animate-pulse rounded-3xl bg-slate-100" />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-3xl border border-rose-200 bg-rose-50 p-6 text-center text-sm text-rose-700">
            <p className="font-semibold">Unable to load explainability data</p>
            <p className="mt-1">{error}</p>
          </div>
        )}

        {!loading && !error && data && (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {data.models.map((model) => (
              <ModelXaiCard key={model.disease_key} model={model} />
            ))}
          </div>
        )}
      </div>

      {/* Explainability Methodology Note */}
      <Card title="About Explainable AI in MediGenie">
        <div className="space-y-4 text-sm text-slate-700">
          <p>
            <strong>SHAP (SHapley Additive exPlanations)</strong> is a game-theory based method that assigns each feature a contribution score 
            for a specific prediction. MediGenie uses SHAP to make clinical AI transparent and auditable.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl bg-indigo-50 p-4 ring-1 ring-indigo-100">
              <p className="font-semibold text-indigo-900">Global Explanations</p>
              <p className="mt-1 text-xs text-indigo-700">
                Mean absolute SHAP values across the entire test set — shows which features matter most for the model overall.
              </p>
            </div>
            <div className="rounded-2xl bg-violet-50 p-4 ring-1 ring-violet-100">
              <p className="font-semibold text-violet-900">Local Explanations</p>
              <p className="mt-1 text-xs text-violet-700">
                Per-prediction SHAP or coefficient values — shows exactly why the model made a specific clinical risk prediction for a patient.
              </p>
            </div>
            <div className="rounded-2xl bg-emerald-50 p-4 ring-1 ring-emerald-100">
              <p className="font-semibold text-emerald-900">Feature Importance</p>
              <p className="mt-1 text-xs text-emerald-700">
                Tree-based feature importance or linear coefficients as fallback when SHAP is not available (e.g., on Windows).
              </p>
            </div>
            <div className="rounded-2xl bg-amber-50 p-4 ring-1 ring-amber-100">
              <p className="font-semibold text-amber-900">Clinical Integration</p>
              <p className="mt-1 text-xs text-amber-700">
                Local explanations are returned inline with every prediction result, making them actionable at point of care.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}
