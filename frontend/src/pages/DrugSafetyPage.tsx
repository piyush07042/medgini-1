import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import toast from "react-hot-toast";
import PageHeading from "../components/PageHeading";
import Card from "../components/Card";
import FormField from "../components/FormField";
import { drugSafetySchema } from "../utils/validation";
import { analyzeDrugSafety } from "../api/drugSafety";
import type { DrugSafetyFormValues } from "../types/form";

type ParsedDrugSafety = {
  overall_risk?: string;
  recommendation?: string;
  interactions?: Array<Record<string, any>>;
  contraindications?: Array<Record<string, any>>;
  allergies?: Array<Record<string, any>>;
  monitoring_advice?: string;
  medications_checked?: string[];
  pregnancy?: Record<string, any>;
};

export default function DrugSafetyPage() {
  const [result, setResult] = useState<string | null>(null);
  const [parsedResult, setParsedResult] = useState<ParsedDrugSafety | null>(null);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<DrugSafetyFormValues>({
    resolver: zodResolver(drugSafetySchema),
  });

  const onSubmit = async (data: DrugSafetyFormValues) => {
    try {
      const response = await analyzeDrugSafety({
        medications: data.medications.split(",").map((item) => item.trim()).filter(Boolean),
        allergies: data.allergies ? data.allergies.split(",").map((item) => item.trim()).filter(Boolean) : [],
      });
      const value = response.data;
      if (typeof value === "string") {
        setResult(value);
        setParsedResult(null);
      } else {
        const parsed = (value as Record<string, any>) || {};
        const assessment = parsed?.drug_safety_assessment || parsed?.data?.drug_safety_assessment || parsed?.assessment || parsed;
        setResult(JSON.stringify(assessment, null, 2));
        setParsedResult({
          overall_risk: assessment?.overall_risk || assessment?.status,
          recommendation: assessment?.recommendation || assessment?.summary,
          interactions: assessment?.interactions || [],
          contraindications: assessment?.contraindications || [],
          allergies: assessment?.allergies || [],
          monitoring_advice: assessment?.monitoring_advice,
          medications_checked: assessment?.medications_checked || [],
          pregnancy: assessment?.pregnancy,
        });
      }
      toast.success("Drug safety analysis complete.");
    } catch (error) {
      toast.error("Unable to analyze medications.");
    }
  };

  const severityTone = (severity?: string) => {
    const value = (severity || "").toLowerCase();
    if (value.includes("high") || value.includes("contraindicated")) return "border-red-200 bg-red-50 text-red-700";
    if (value.includes("moderate") || value.includes("warning")) return "border-amber-200 bg-amber-50 text-amber-700";
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  };

  const summaryCards = useMemo(() => [
    { label: "Overall risk", value: parsedResult?.overall_risk || "Pending" },
    { label: "Medication count", value: parsedResult?.medications_checked?.length ? String(parsedResult.medications_checked.length) : "0" },
    { label: "Interactions", value: parsedResult?.interactions?.length ? String(parsedResult.interactions.length) : "0" },
  ], [parsedResult]);

  return (
    <div className="space-y-10">
      <PageHeading title="Drug Safety" description="Identify medication risk patterns and analyze patient-specific interactions." />
      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Drug safety analysis">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <FormField label="Medications" placeholder="Aspirin, Metformin" register={register("medications")} error={errors.medications} description="Comma-separated medication list." />
            <FormField label="Allergies" placeholder="Penicillin" register={register("allergies")} error={errors.allergies} description="Comma-separated allergy list." />
            <button type="submit" disabled={isSubmitting} className="rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300">
              {isSubmitting ? "Analyzing..." : "Analyze medications"}
            </button>
          </form>
        </Card>

        <Card title="Assessment result">
          {result ? (
            <div className="space-y-5">
              <div className="grid gap-3 sm:grid-cols-3">
                {summaryCards.map((item) => (
                  <div key={item.label} className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{item.label}</p>
                    <p className="mt-2 text-sm font-semibold text-slate-900">{item.value}</p>
                  </div>
                ))}
              </div>

              {parsedResult?.recommendation ? (
                <div className="rounded-3xl border border-brand-200 bg-brand-50 p-4 text-sm text-slate-700">
                  <p className="font-semibold text-slate-900">Clinical recommendation</p>
                  <p className="mt-2">{parsedResult.recommendation}</p>
                </div>
              ) : null}

              <div className="space-y-3">
                <p className="text-sm font-semibold text-slate-900">Interactions</p>
                {parsedResult?.interactions?.length ? parsedResult.interactions.map((interaction, index) => (
                  <div key={index} className={`rounded-3xl border p-4 ${severityTone(interaction.severity)}`}>
                    <p className="font-semibold">{interaction.drugs_involved?.join(" + ") || "Interaction"}</p>
                    <p className="mt-2 text-sm">{interaction.explanation || interaction.recommendation}</p>
                    {interaction.recommendation ? <p className="mt-2 text-sm font-medium">{interaction.recommendation}</p> : null}
                  </div>
                )) : <p className="text-sm text-slate-500">No interactions detected.</p>}
              </div>

              <div className="space-y-3">
                <p className="text-sm font-semibold text-slate-900">Contraindications</p>
                {parsedResult?.contraindications?.length ? parsedResult.contraindications.map((item, index) => (
                  <div key={index} className={`rounded-3xl border p-4 ${severityTone(item.severity)}`}>
                    <p className="font-semibold">{item.medication || item.condition}</p>
                    <p className="mt-2 text-sm">{item.explanation || item.recommendation}</p>
                  </div>
                )) : <p className="text-sm text-slate-500">No contraindications flagged.</p>}
              </div>

              <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-semibold text-slate-900">Printable interaction report</p>
                <p className="mt-2">Use this summary to share or print a concise medication-risk review for the care team.</p>
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="mt-4 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
                >
                  Print report
                </button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Enter medications to receive a safety assessment from the backend.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
