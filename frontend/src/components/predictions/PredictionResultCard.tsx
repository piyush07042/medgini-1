import RiskBadge from "./RiskBadge";
import ConfidenceMeter from "./ConfidenceMeter";
import RecommendationPanel from "./RecommendationPanel";
import DrugSafetyPanel from "./DrugSafetyPanel";
import ExplainabilityPanel from "./ExplainabilityPanel";

export default function PredictionResultCard({
  result,
}: {
  result: Record<string, any>;
}) {
  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-3">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-400">Result</p>
            <h2 className="text-2xl font-semibold text-slate-900">{result.disease ?? "Prediction"}</h2>
            <p className="text-sm text-slate-500">Prediction summary from the backend model response.</p>
          </div>

          <div className="space-y-3 rounded-3xl border border-slate-100 bg-slate-50 p-5">
            <p className="text-sm font-semibold text-slate-900">Prediction</p>
            <p className="text-4xl font-semibold text-slate-900">{result.prediction}</p>
            <RiskBadge risk={result.confidence_label ?? "Unknown"} />
          </div>

          <div className="space-y-4">
            <div className="rounded-3xl border border-slate-100 bg-slate-50 p-5">
              <p className="text-sm text-slate-500">Probability</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900">{typeof result.probability === "number" ? result.probability.toFixed(2) : result.probability}</p>
            </div>
            <div className="rounded-3xl border border-slate-100 bg-slate-50 p-5">
              <p className="text-sm text-slate-500">Confidence</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900">{typeof result.confidence === "number" ? result.confidence.toFixed(2) : result.confidence}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <h3 className="mb-4 text-lg font-semibold text-slate-900">Explainability</h3>
          <ExplainabilityPanel explanations={result.explanations} />
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <h3 className="mb-4 text-lg font-semibold text-slate-900">Recommendations</h3>
          <RecommendationPanel recommendations={result.recommendations} />
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
          <h3 className="mb-4 text-lg font-semibold text-slate-900">Drug safety</h3>
          <DrugSafetyPanel drugSafety={result.drug_safety} />
        </div>
      </div>

      <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-soft">
        <h3 className="mb-4 text-lg font-semibold text-slate-900">Generated report</h3>
        {result.final_report ? (
          <pre className="max-h-[420px] overflow-auto rounded-3xl bg-slate-950 p-4 text-sm text-slate-100">
            {JSON.stringify(result.final_report, null, 2)}
          </pre>
        ) : (
          <p className="text-sm text-slate-500">No generated report data was included in the response.</p>
        )}
      </div>
    </div>
  );
}
