import { useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { type DefaultValues, type FieldValues, useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { Info } from "lucide-react";
import PageHeading from "../../components/PageHeading";
import Card from "../../components/Card";
import PredictionForm from "./PredictionForm";
import PredictionPanel from "./PredictionPanel";
import PredictionResultView from "./PredictionResultView";
import PredictionHistory from "./PredictionHistory";
import { usePredictionContext } from "../../hooks/usePredictionContext";
import { addPredictionHistory, getPredictionHistory } from "../../utils/predictionHistory";
import { buildPredictionFormValues } from "../../utils/predictionPrefill";
import { saveDashboardPrediction } from "../../api/dashboard";
import { invalidateDashboardCache } from "../../services/dashboardService";
import type { PredictionHistoryItem } from "../../utils/predictionHistory";
import type { Patient } from "../../types/api";
import type { ZodType } from "zod";

export type PredictionField<TValues extends FieldValues> = {
  name: keyof TValues;
  label: string;
  placeholder?: string;
  type?: "text" | "number";
  tooltip?: string;
  range?: string;
  step?: string;
};

type PredictionPageShellProps<TValues extends FieldValues, TResponse extends Record<string, any>> = {
  title: string;
  description: string;
  schema: ZodType<TValues, any>;
  defaultValues: TValues;
  fields: Array<PredictionField<TValues>>;
  predict: (payload: TValues) => Promise<TResponse>;
  successMessage?: string;
  submitLabel?: string;
};

export default function PredictionPageShell<
  TValues extends Record<string, any>,
  TResponse extends Record<string, any>,
>({
  title,
  description,
  schema,
  defaultValues,
  fields,
  predict,
  successMessage,
  submitLabel = "Run prediction",
}: PredictionPageShellProps<TValues, TResponse>) {
  const { patientId, patient, patientContext, extractedMetrics } = usePredictionContext();
  const [result, setResult] = useState<TResponse | null>(null);
  const [history, setHistory] = useState<PredictionHistoryItem[]>([]);
  const [prefillApplied, setPrefillApplied] = useState(false);

  const currentPatient = useMemo<Patient | null>(() => {
    if (patient) return patient;
    if (!patientContext) return null;
    return {
      id: Number(patientContext.id ?? -1),
      doctor_id: Number(patientContext.doctor_id ?? 0),
      first_name: String(patientContext.first_name ?? patientContext.name ?? "Patient"),
      last_name: String(patientContext.last_name ?? ""),
      age: Number(patientContext.age ?? 0),
      gender: String(patientContext.gender ?? "Unknown"),
      medical_history: patientContext.medical_history,
      allergies: Array.isArray(patientContext.allergies) ? patientContext.allergies : [],
      current_medications: Array.isArray(patientContext.current_medications) ? patientContext.current_medications : [],
      created_at: String(patientContext.created_at ?? new Date().toISOString()),
    };
  }, [patient, patientContext]);

  const prefillValues = useMemo(() => {
    return buildPredictionFormValues(defaultValues, extractedMetrics, patientContext);
  }, [defaultValues, extractedMetrics, patientContext]);

  const queryClient = useQueryClient();
  const { register, handleSubmit, reset, formState } = useForm<TValues>({
    defaultValues: prefillValues as DefaultValues<TValues>,
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (!prefillApplied && (Object.keys(extractedMetrics ?? {}).length > 0 || patientContext)) {
      reset(prefillValues);
      setPrefillApplied(true);
    }
  }, [prefillApplied, extractedMetrics, patientContext, prefillValues, reset]);

  useEffect(() => {
    if (patientId) {
      setHistory(getPredictionHistory(patientId));
    } else {
      setHistory([]);
    }
  }, [patientId]);

  const onSubmit = async (values: TValues) => {
    try {
      const prediction = await predict(values);
      setResult(prediction);
      toast.success(successMessage ?? `${title} completed.`);

      if (patientId) {
        const summary = Array.isArray(prediction.recommendations)
          ? prediction.recommendations.slice(0, 2).map((item) => (typeof item === "string" ? item : item.recommendation || JSON.stringify(item))).join("; ")
          : undefined;

        const historyItem: PredictionHistoryItem = {
          id: `${patientId}-${title}-${Date.now()}`,
          patientId,
          disease: prediction.disease ?? title,
          createdAt: new Date().toISOString(),
          prediction: prediction.prediction ?? "unknown",
          probability: typeof prediction.probability === "number" ? prediction.probability : Number(prediction.probability) || 0,
          confidence: typeof prediction.confidence === "number" ? prediction.confidence : Number(prediction.confidence) || 0,
          confidenceLabel: prediction.confidence_label ?? null,
          summary,
          result: prediction,
        };

        addPredictionHistory(historyItem);
        setHistory((current) => [historyItem, ...current]);

        try {
          await saveDashboardPrediction({
            patient_id: patientId,
            risk_assessment: prediction,
            rag_evidence: Array.isArray(prediction.evidence) ? prediction.evidence : [],
            drug_safety_alerts: prediction.drug_safety ?? {},
            clinical_summary: prediction.final_report?.clinical_summary ?? "",
            clinical_intelligence: prediction.final_report?.clinical_intelligence ?? prediction.clinical_intelligence ?? {},
          });
          invalidateDashboardCache();
          queryClient.invalidateQueries({ queryKey: ["dashboard"] });
        } catch (innerError) {
          console.warn("Unable to persist prediction to dashboard:", innerError);
        }
      }
    } catch (error) {
      toast.error("Prediction failed. Check inputs or backend status.");
    }
  };

  const onReset = () => {
    reset(defaultValues);
    setResult(null);
  };

  return (
    <div className="space-y-10">
      <PageHeading title={title} description={description} />

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.9fr]">
        <Card title="Model inputs">
          <PredictionForm handleSubmit={handleSubmit} onSubmit={onSubmit} isSubmitting={formState.isSubmitting} onReset={onReset} submitLabel={submitLabel}>
            <div className="grid gap-5">
              {fields.map((field) => (
                <div key={String(field.name)}>
                  <div className="flex items-center gap-2">
                    <label className="block text-sm font-medium text-slate-700">{field.label}</label>
                    {field.tooltip ? (
                      <div className="group relative">
                        <Info className="h-4 w-4 text-slate-400" />
                        <div className="pointer-events-none absolute left-0 top-6 z-10 hidden w-64 rounded-2xl border border-slate-200 bg-white p-3 text-xs text-slate-600 shadow-lg group-hover:block">
                          {field.tooltip}
                        </div>
                      </div>
                    ) : null}
                  </div>
                  {field.range ? <p className="mt-1 text-xs text-slate-500">Range: {field.range}</p> : null}
                  <input
                    type={field.type ?? "text"}
                    placeholder={field.placeholder}
                    step={field.step}
                    {...register(field.name as any)}
                    className={`mt-2 block w-full rounded-2xl border bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition ${
                      formState.errors[field.name] 
                        ? "border-rose-300 focus:border-rose-500 focus:ring-2 focus:ring-rose-100" 
                        : "border-slate-200 focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
                    }`}
                  />
                  {formState.errors[field.name] && (
                    <p className="mt-1.5 text-xs font-medium text-rose-600">
                      {formState.errors[field.name]?.message as string}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </PredictionForm>
        </Card>

        <div className="space-y-6">
          <PredictionPanel title="Patient context">
            {currentPatient ? (
              <div className="space-y-3 text-sm text-slate-700">
                <p className="text-base font-semibold text-slate-900">{currentPatient.first_name} {currentPatient.last_name}</p>
                <p>Age: {currentPatient.age}</p>
                <p>Gender: {currentPatient.gender}</p>
                <p>Allergies: {currentPatient.allergies?.join(", ") || "None"}</p>
                <p>Medications: {currentPatient.current_medications?.join(", ") || "None"}</p>
                <p className="text-slate-500">Created: {new Date(currentPatient.created_at).toLocaleString()}</p>
              </div>
            ) : (
              <p className="text-sm text-slate-500">No saved patient context is available. Use report upload or add a patient ID to your URL.</p>
            )}
          </PredictionPanel>

          <PredictionPanel title="Previous predictions">
            <PredictionHistory history={history} />
          </PredictionPanel>

          {Object.keys(extractedMetrics ?? {}).length > 0 ? (
            <PredictionPanel title="OCR extracted metrics">
              <pre className="max-h-[280px] overflow-auto rounded-3xl bg-slate-950 p-4 text-sm text-slate-100">
                {JSON.stringify(extractedMetrics, null, 2)}
              </pre>
            </PredictionPanel>
          ) : null}
        </div>
      </div>

      <div className="mt-8">
        {result ? (
          <PredictionResultView
            result={result}
            patient={patient}
            patientId={patientId}
            timestamp={new Date().toLocaleString()}
            onNewPrediction={onReset}
          />
        ) : (
          <PredictionPanel title="Prediction result">
            <p className="text-sm text-slate-500">Submit the form to run a prediction and view the model result, recommendations, and report output here.</p>
          </PredictionPanel>
        )}
      </div>
    </div>
  );
}
