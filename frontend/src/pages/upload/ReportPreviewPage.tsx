import { useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import PageHeading from "../../components/PageHeading";
import Card from "../../components/Card";
import { UploadReportResponse } from "../../types/api";

export default function ReportPreviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as { result?: UploadReportResponse; fileName?: string } | null;
  const result = state?.result;
  const fileName = state?.fileName;
  const [editedText, setEditedText] = useState("");
  const [savedCorrection, setSavedCorrection] = useState(false);

  if (!result) {
    return (
      <div className="space-y-10">
        <PageHeading title="Report preview" description="No report data is available yet." />
        <Card title="No report available">
          <p className="text-sm text-slate-500">Please upload a report first, then use this page to inspect the processed result.</p>
          <button
            type="button"
            onClick={() => navigate("/upload-report")}
            className="mt-4 w-full rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700"
          >
            Upload a new report
          </button>
        </Card>
      </div>
    );
  }

  const workflow = result.workflow_state || (result as any)?.data?.workflow_state || (result as any)?.data;

  const extractedMetrics = useMemo(() => {
    const direct = workflow?.extracted_metrics;
    if (direct && typeof direct === "object" && Object.keys(direct).length > 0) {
      return direct as Record<string, unknown>;
    }
    const ocrRes = workflow?.ocr_result;
    if (Array.isArray(ocrRes) && ocrRes.length > 0 && ocrRes[0]?.metrics) {
      return ocrRes[0].metrics as Record<string, unknown>;
    }
    if (ocrRes && typeof ocrRes === "object" && (ocrRes as any).metrics) {
      return (ocrRes as any).metrics as Record<string, unknown>;
    }
    return {} as Record<string, unknown>;
  }, [workflow]);

  const extractedMetricsCount = Object.keys(extractedMetrics).length;

  const diseaseRisk = useMemo(() => {
    const direct = workflow?.disease_risk;
    if (direct && typeof direct === "object" && Object.keys(direct).length > 0) {
      return direct as Record<string, any>;
    }
    const recRisk = workflow?.recommendations?.[0]?.risk_summary || workflow?.recommendations?.[0]?.risk_analysis;
    if (recRisk && typeof recRisk === "object" && Object.keys(recRisk).length > 0) {
      return recRisk as Record<string, any>;
    }
    return (direct || {}) as Record<string, any>;
  }, [workflow]);

  const patientContext = useMemo(() => {
    const direct = workflow?.patient;
    if (direct && typeof direct === "object" && Object.keys(direct).length > 0) {
      return direct as Record<string, any>;
    }
    const summary = workflow?.patient_summary;
    if (summary && typeof summary === "object" && Object.keys(summary).length > 0) {
      return summary as Record<string, any>;
    }
    const history = workflow?.patient_history;
    if (history && typeof history === "object" && Object.keys(history).length > 0) {
      return history as Record<string, any>;
    }
    if (extractedMetricsCount > 0) {
      const derived: Record<string, any> = {};
      for (const [k, v] of Object.entries(extractedMetrics)) {
        if (["patient_id", "id", "age", "sex", "gender", "bmi", "glucose", "cholesterol", "systolic_bp", "diastolic_bp"].includes(k)) {
          derived[k] = v;
        }
      }
      if (Object.keys(derived).length > 0) return derived;
    }
    return (direct || {}) as Record<string, any>;
  }, [workflow, extractedMetrics, extractedMetricsCount]);

  const ocrText = useMemo(() => {
    const rawText = workflow?.report_text ?? workflow?.ocr_result?.text ?? workflow?.ocr_result?.full_text ?? "";
    if (typeof rawText === "string") {
      return rawText;
    }
    return JSON.stringify(rawText, null, 2);
  }, [workflow]);

  useMemo(() => {
    setEditedText(ocrText);
  }, [ocrText]);

  const handleSaveCorrection = () => {
    setSavedCorrection(true);
    const nextWorkflow = {
      ...(workflow ?? {}),
      report_text: editedText,
      metadata: {
        ...(workflow?.metadata ?? {}),
        ocr_correction_saved: true,
      },
    };

    localStorage.setItem("medigenie_ocr_correction", JSON.stringify({ fileName, editedText, savedAt: new Date().toISOString() }));
    navigate("/upload-report/preview", {
      state: {
        result: { ...result, workflow_state: nextWorkflow },
        fileName,
      },
      replace: true,
    });
  };

  return (
    <div className="space-y-10">
      <PageHeading title="Report preview" description="Review the extracted OCR text, AI risk analysis, and recommendations." />

      <div className="grid gap-6 xl:grid-cols-3">
        <Card title="Report summary">
          <div className="space-y-3 text-sm text-slate-700">
            <p>
              <span className="font-semibold">File</span>: {fileName ?? "Uploaded report"}
            </p>
            <p>
              <span className="font-semibold">Workflow status</span>: {workflow?.metadata?.workflow_status ?? "completed"}
            </p>
            <p>
              <span className="font-semibold">Warnings</span>: {workflow?.warnings?.length ?? 0}
            </p>
            <p>
              <span className="font-semibold">Errors</span>: {workflow?.errors?.length ?? 0}
            </p>
            <p>
              <span className="font-semibold">Extracted metrics</span>: {extractedMetricsCount}
            </p>
            {extractedMetricsCount > 0 ? (
              <div className="mt-3 rounded-2xl bg-slate-50 p-3 text-xs">
                <p className="font-semibold text-slate-900 mb-2">Metrics Preview</p>
                <div className="grid grid-cols-2 gap-1.5 text-slate-600">
                  {Object.entries(extractedMetrics).slice(0, 6).map(([k, v]) => (
                    <p key={k} className="truncate">
                      <span className="font-medium text-slate-800">{k}:</span> {String(v)}
                    </p>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </Card>

        <Card title="Patient context">
          {Object.keys(patientContext).length > 0 ? (
            <div className="space-y-3">
              <div className="rounded-2xl bg-slate-50 p-3 space-y-2 text-sm text-slate-800">
                {patientContext.first_name || patientContext.last_name || patientContext.name ? (
                  <p className="font-bold text-slate-900 text-base">
                    {[patientContext.first_name, patientContext.last_name].filter(Boolean).join(" ") || patientContext.name}
                  </p>
                ) : null}
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
                  {patientContext.patient_id || patientContext.id ? <p><span className="font-semibold">ID:</span> {String(patientContext.patient_id || patientContext.id)}</p> : null}
                  {patientContext.age !== undefined ? <p><span className="font-semibold">Age:</span> {String(patientContext.age)} yrs</p> : null}
                  {patientContext.gender || patientContext.sex ? <p><span className="font-semibold">Gender:</span> {String(patientContext.gender || patientContext.sex)}</p> : null}
                  {patientContext.bmi !== undefined ? <p><span className="font-semibold">BMI:</span> {String(patientContext.bmi)}</p> : null}
                </div>
              </div>

              <details className="text-xs text-slate-500">
                <summary className="cursor-pointer font-medium hover:text-slate-700">View patient details JSON</summary>
                <pre className="mt-2 max-h-[160px] overflow-auto rounded-2xl bg-slate-950 p-3 text-slate-100">
                  {JSON.stringify(patientContext, null, 2)}
                </pre>
              </details>
            </div>
          ) : (
            <p className="text-sm text-slate-500">No patient context was provided with this upload.</p>
          )}
        </Card>

        <Card title="Risk analysis">
          {Object.keys(diseaseRisk).length > 0 ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Condition</p>
                  <p className="mt-1 text-base font-bold text-slate-900">
                    {diseaseRisk.condition || diseaseRisk.disease || "Clinical Risk Assessment"}
                  </p>
                </div>
                <span className={`rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider ${
                  (diseaseRisk.risk_category || diseaseRisk.risk_level || "").toLowerCase() === "high" || (diseaseRisk.prediction || "").toLowerCase().includes("high")
                    ? "bg-red-100 text-red-700"
                    : (diseaseRisk.risk_category || diseaseRisk.risk_level || "").toLowerCase() === "medium" || (diseaseRisk.prediction || "").toLowerCase().includes("medium")
                    ? "bg-amber-100 text-amber-700"
                    : "bg-emerald-100 text-emerald-700"
                }`}>
                  {diseaseRisk.prediction || diseaseRisk.risk_category || diseaseRisk.risk_level || "Assessed"}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 rounded-2xl bg-slate-50 p-3">
                <div>
                  <p className="text-xs text-slate-500 font-medium">Probability</p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {(() => {
                      const raw = diseaseRisk.probability ?? diseaseRisk.risk_score ?? diseaseRisk.estimated_risk_score_percent;
                      if (raw === undefined || raw === null) return "N/A";
                      const num = Number(raw);
                      if (isNaN(num)) return String(raw);
                      return `${(num <= 1 ? num * 100 : num).toFixed(1)}%`;
                    })()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500 font-medium">Confidence</p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">
                    {(() => {
                      const raw = diseaseRisk.confidence ?? diseaseRisk.confidence_label;
                      if (raw === undefined || raw === null) return "N/A";
                      const num = Number(raw);
                      if (isNaN(num)) return String(raw);
                      return `${(num <= 1 ? num * 100 : num).toFixed(1)}%`;
                    })()}
                  </p>
                </div>
              </div>

              {diseaseRisk.supporting_factors?.length ? (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1.5">Supporting Factors</p>
                  <ul className="space-y-1 text-xs text-slate-700 list-disc list-inside">
                    {diseaseRisk.supporting_factors.map((factor: string, idx: number) => (
                      <li key={idx}>{factor}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <details className="text-xs text-slate-500">
                <summary className="cursor-pointer font-medium hover:text-slate-700">View raw risk JSON</summary>
                <pre className="mt-2 max-h-[160px] overflow-auto rounded-2xl bg-slate-950 p-3 text-slate-100">
                  {JSON.stringify(diseaseRisk, null, 2)}
                </pre>
              </details>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Risk analysis was not produced for this report.</p>
          )}
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="OCR result">
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm text-slate-500">Edit extracted OCR text before moving to the next step.</p>
              <button
                type="button"
                onClick={handleSaveCorrection}
                className="rounded-2xl border border-brand-600 bg-brand-50 px-3 py-2 text-sm font-semibold text-brand-700 transition hover:bg-brand-100"
              >
                Save correction
              </button>
            </div>
            {ocrText ? (
              <textarea
                rows={12}
                value={editedText}
                onChange={(event) => {
                  setEditedText(event.target.value);
                  setSavedCorrection(false);
                }}
                className="min-h-[260px] w-full rounded-3xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
              />
            ) : (
              <p className="text-sm text-slate-500">No OCR output was extracted from this report.</p>
            )}
            {savedCorrection ? <p className="text-sm text-emerald-600">Correction saved locally for this session.</p> : null}
          </div>
        </Card>

        <Card title="Recommendations">
          {workflow?.recommendations?.length ? (
            <div className="space-y-3 text-sm text-slate-700">
              {workflow.recommendations.map((recommendation: any, index: number) => (
                <div key={index} className="rounded-2xl bg-slate-50 p-4">
                  <pre className="whitespace-pre-wrap text-sm text-slate-800">{JSON.stringify(recommendation, null, 2)}</pre>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-500">No recommendations were generated for this upload.</p>
          )}
        </Card>
      </div>

      <Card title="Raw workflow response">
        <pre className="max-h-[420px] overflow-auto rounded-3xl bg-slate-950 p-4 text-sm text-slate-100">
          {JSON.stringify(result, null, 2)}
        </pre>
      </Card>

      <div className="flex flex-col gap-3 lg:flex-row">
        <button
          type="button"
          onClick={() => navigate("/upload-report")}
          className="w-full rounded-2xl bg-slate-100 px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-200 lg:w-auto"
        >
          Upload another report
        </button>
        <button
          type="button"
          onClick={() => navigate("/predictions", { state: { result } })}
          className="w-full rounded-2xl border border-brand-500 bg-white px-4 py-3 text-sm font-semibold text-brand-700 transition hover:bg-brand-50 lg:w-auto"
        >
          Run disease prediction
        </button>
        <button
          type="button"
          onClick={() => navigate("/upload-report/processing", {
            state: {
              status: "completed",
              fileName,
              progress: 100,
              startedAt: new Date().toISOString(),
            },
          })}
          className="w-full rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 lg:w-auto"
        >
          View processing status
        </button>
      </div>
    </div>
  );
}
