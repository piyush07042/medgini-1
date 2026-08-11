import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import api from "../../api/client";
import { getReportPdfDownloadUrl } from "../../api/reports";
import PredictionPanel from "./PredictionPanel";
import RiskBadge from "./RiskBadge";
import ConfidenceMeter from "./ConfidenceMeter";
import RecommendationPanel from "./RecommendationPanel";
import ExplainabilityPanel from "./ExplainabilityPanel";
import DrugSafetyPanel from "./DrugSafetyPanel";
import ClinicalGuidelineCard from "./ClinicalGuidelineCard";
import { getGuidelineFor } from "../../utils/guidelines";


import type { Patient } from "../../types/api";

export default function PredictionResultView({
  result,
  patient,
  patientId,
  timestamp,
  onNewPrediction,
}: {
  result: Record<string, any>;
  patient?: Patient | null;
  patientId?: number;
  timestamp: string;
  onNewPrediction: () => void;
}) {
  const [showDetails, setShowDetails] = useState(false);
  const navigate = useNavigate();
  const confidenceValue = typeof result.confidence === "number" ? result.confidence : Number(result.confidence) || 0;
  const riskLabel = result.confidence_label || result.risk || "Unknown";

  const downloadPdf = async () => {
    try {
      const reportPatientId = patient?.id ?? patientId;
      if (!reportPatientId) {
        toast.error("Patient ID not available for PDF generation.");
        return;
      }
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
      window.open(`${API_BASE_URL}/reports/medigenie/${reportPatientId}/pdf`, "_blank");
    } catch (e) {
      toast.error("Unable to download PDF report.");
    }
  };

  const printReport = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      <PredictionPanel title="Prediction summary">
        <div className="flex flex-col gap-6">
          <div className="space-y-3">
            <p className="text-sm text-slate-500">Disease</p>
            <p className="text-lg font-semibold text-slate-900">{result.disease ?? "Unknown"}</p>

            <div className="mt-3 text-sm text-slate-600">
              <p className="font-medium">Patient</p>
              {patient ? (
                <p>{patient.first_name} {patient.last_name} · {patient.age}y · {patient.gender}</p>
              ) : (
                <p>No patient context</p>
              )}
            </div>
          </div>

          <div className="grid gap-3">
            <div className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
              <div>
                <p className="text-xs text-slate-500">Risk</p>
                <div className="mt-1"><RiskBadge risk={riskLabel} /></div>
              </div>
              <div>
                <p className="text-xs text-slate-500">Probability</p>
                <p className="mt-1 text-xl font-semibold text-slate-900">{typeof result.probability === "number" ? (result.probability * 100).toFixed(1) + "%" : result.probability ?? "N/A"}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Confidence</p>
                <div className="mt-1"><ConfidenceMeter confidence={confidenceValue} compact /></div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-3">
              <p className="text-sm text-slate-500">Top recommendations</p>
              <ul className="mt-2 max-h-36 divide-y divide-slate-100 overflow-auto text-sm text-slate-700">
                {(Array.isArray(result.recommendations) ? result.recommendations.slice(0, 5) : []).map((r: any, i: number) => (
                  <li key={i} className="py-2">{typeof r === "string" ? r : r.recommendation ?? JSON.stringify(r)}</li>
                ))}
                {!result.recommendations || result.recommendations.length === 0 ? <li className="py-2 text-slate-500">No recommendations provided.</li> : null}
              </ul>
            </div>
            {/* Guideline-based recommendations (Clinical Intelligence) */}
            {(() => {
              const clinical = result.clinical_intelligence || result.final_report?.clinical_intelligence;
              if (!clinical || Object.keys(clinical).length === 0) return null;

              return (
                <div className="rounded-2xl border border-slate-200 bg-white p-4">
                  <p className="text-sm font-semibold text-slate-900 mb-4">Clinical Intelligence</p>
                  <div className="space-y-4">
                    {Object.entries(clinical).map(([key, value]) => {
                      if (Array.isArray(value)) {
                        return (
                          <div key={key}>
                            <p className="text-sm font-medium text-slate-900">{key}</p>
                            <ul className="mt-1 list-inside list-disc text-sm text-slate-700">
                              {value.map((item, i) => {
                                if (typeof item === 'object' && item !== null) {
                                  const text = item.drug && item.condition && item.action 
                                    ? `Drug: ${item.drug} | If: ${item.condition} | Action: ${item.action}`
                                    : JSON.stringify(item);
                                  return <li key={i}>{text}</li>;
                                }
                                return <li key={i}>{String(item)}</li>;
                              })}
                            </ul>
                          </div>
                        );
                      }
                      return (
                        <div key={key}>
                          <p className="text-sm font-medium text-slate-900 inline">{key}: </p>
                          <span className="text-sm text-slate-700">{typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })()}
          </div>
        </div>

        <div className="mt-4 flex gap-3">
          <button onClick={() => setShowDetails((s) => !s)} className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700">
            {showDetails ? "Hide details" : "View full report"}
          </button>
          <button onClick={downloadPdf} className="rounded-2xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white">Download PDF</button>
          <button onClick={onNewPrediction} className="rounded-2xl border border-slate-200 bg-slate-900 px-4 py-2 text-sm font-semibold text-white">Run another</button>
        </div>
      </PredictionPanel>

      {showDetails ? (
        <div className="space-y-6">
          {patient ? (
            <PredictionPanel title="Patient summary">
              <div className="space-y-3 text-sm text-slate-700">
                <p className="font-semibold text-slate-900">{patient.first_name} {patient.last_name}</p>
                <p>Age: {patient.age}</p>
                <p>Gender: {patient.gender}</p>
                <p className="text-slate-500">Created: {new Date(patient.created_at).toLocaleString()}</p>
              </div>
            </PredictionPanel>
          ) : null}

          <div className="grid gap-6 xl:grid-cols-2">
            <div className="space-y-6">
              <ClinicalGuidelineCard clinicalIntel={result.clinical_intelligence || result.final_report?.clinical_intelligence} />
              <PredictionPanel title="Explainability & feature importance">
                <ExplainabilityPanel explanations={result.explanations} />
                {result.feature_importance ? (
                  <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm font-semibold text-slate-900">Feature importance</p>
                    <pre className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{JSON.stringify(result.feature_importance, null, 2)}</pre>
                  </div>
                ) : null}
                {result.shap || result.shap_values ? (
                  <div className="mt-6 rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-sm font-semibold text-slate-900">SHAP explanation</p>
                    <pre className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-700">{JSON.stringify(result.shap || result.shap_values, null, 2)}</pre>
                  </div>
                ) : null}
              </PredictionPanel>
            </div>


            <PredictionPanel title="Recommendations & drug safety">
              <RecommendationPanel recommendations={result.recommendations} />
              <div className="mt-6">
                <DrugSafetyPanel drugSafety={result.drug_safety} />
              </div>
            </PredictionPanel>
          </div>

          <PredictionPanel title="Generated AI report">
            {result.final_report ? (
              <pre className="max-h-[420px] overflow-auto rounded-3xl bg-slate-950 p-4 text-sm text-slate-100">
                {JSON.stringify(result.final_report, null, 2)}
              </pre>
            ) : (
              <p className="text-sm text-slate-500">No generated AI report was returned by the backend.</p>
            )}
          </PredictionPanel>
        </div>
      ) : null}
    </div>
  );
}
