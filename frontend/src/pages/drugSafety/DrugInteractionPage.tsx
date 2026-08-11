import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import PageHeading from "../../components/PageHeading";
import Card from "../../components/Card";
import DrugSearch from "../../components/drugSafety/DrugSearch";
import DrugInteractionCard from "../../components/drugSafety/DrugInteractionCard";
import WarningCard from "../../components/drugSafety/WarningCard";
import DrugRecommendation from "../../components/drugSafety/DrugRecommendation";
import { analyzeDrugSafety } from "../../api/drugSafety";
import { getPatientDetails } from "../../api/patients";
import type { DrugSafetyAssessmentResult, Patient } from "../../types/api";

export default function DrugInteractionPage() {
  const location = useLocation();
  const state = location.state as { medications?: string[]; allergies?: string; patientId?: number } | null;

  const [selectedMedications, setSelectedMedications] = useState<string[]>(state?.medications ?? []);
  const [allergies, setAllergies] = useState(state?.allergies ?? "");
  const [assessment, setAssessment] = useState<DrugSafetyAssessmentResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const patientId = Number.isInteger(state?.patientId ?? NaN) ? state?.patientId ?? null : null;

  const patientQuery = useQuery({
    queryKey: ["patientDetails", patientId],
    queryFn: () => (patientId ? getPatientDetails(patientId) : Promise.resolve(null)),
    enabled: Boolean(patientId),
    staleTime: 1000 * 60 * 5,
  });

  const patient = patientQuery.data as Patient | null;

  useEffect(() => {
    if (state?.medications?.length && !assessment) {
      handleAnalyze();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAddMedication = (drug: string) => {
    const normalized = drug.trim().replace(/\s+/g, " ");
    if (!normalized || selectedMedications.some((item) => item.toLowerCase() === normalized.toLowerCase())) {
      return;
    }
    setSelectedMedications((current) => [...current, normalized]);
  };

  const handleRemoveMedication = (drug: string) => {
    setSelectedMedications((current) => current.filter((item) => item.toLowerCase() !== drug.toLowerCase()));
  };

  const handleAnalyze = async () => {
    if (!selectedMedications.length) {
      setAnalysisError("Add at least one medication before running interaction checks.");
      setAssessment(null);
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const response = await analyzeDrugSafety({
        medications: selectedMedications,
        allergies: allergies
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });

      const data = response.data?.drug_safety_assessment;
      if (!data) {
        throw new Error("Unexpected server response.");
      }

      setAssessment(data);
    } catch {
      setAssessment(null);
      setAnalysisError("Unable to perform interaction analysis with the selected medications.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="space-y-10">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <PageHeading title="Drug Interaction Checker" description="Focus on drug-drug interactions, contraindications, and severity details." />
        <Link
          to="/drug-safety"
          className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
        >
          Back to Drug Safety
        </Link>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <section className="space-y-6">
          <Card title="Interaction input">
            <div className="space-y-5">
              <DrugSearch
                selected={selectedMedications}
                onAdd={handleAddMedication}
                onRemove={handleRemoveMedication}
                suggestions={[]}
              />

              <label className="block text-sm font-medium text-slate-700">
                Patient allergies
                <input
                  type="text"
                  value={allergies}
                  onChange={(event) => setAllergies(event.target.value)}
                  placeholder="Penicillin, Sulfa"
                  className="mt-2 w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                />
              </label>

              <div className="grid gap-3 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                  className="rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {isAnalyzing ? "Checking interactions..." : "Analyze interactions"}
                </button>
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Patient</p>
                  <p className="mt-2 text-base font-semibold text-slate-900">{patient ? `${patient.first_name} ${patient.last_name}` : "No patient selected"}</p>
                  <p className="text-sm text-slate-500">{patient ? `ID ${patient.id}` : "Use drug safety page query params to prefill a patient."}</p>
                </div>
              </div>

              {analysisError ? (
                <div className="rounded-3xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                  {analysisError}
                </div>
              ) : null}
            </div>
          </Card>

          <Card title="Critical interaction summary">
            {assessment ? (
              <div className="space-y-5">
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-5">
                  <p className="text-sm text-slate-500">Overall interaction risk</p>
                  <p className="mt-3 text-3xl font-semibold text-slate-900">{assessment.overall_risk}</p>
                  <p className="mt-2 text-sm text-slate-500">{assessment.recommendation}</p>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-3xl border border-slate-200 bg-white p-5">
                    <p className="text-sm text-slate-500">Interactions found</p>
                    <p className="mt-3 text-2xl font-semibold text-slate-900">{assessment.interactions.length}</p>
                  </div>
                  <div className="rounded-3xl border border-slate-200 bg-white p-5">
                    <p className="text-sm text-slate-500">Contraindications</p>
                    <p className="mt-3 text-2xl font-semibold text-slate-900">{assessment.contraindications.length}</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">Run an interaction review to see critical drug safety insights.</p>
            )}
          </Card>
        </section>

        <section className="space-y-6">
          <Card title="Interaction details">
            {assessment ? (
              assessment.interactions.length ? (
                <div className="space-y-4">
                  {assessment.interactions.map((interaction, index) => (
                    <DrugInteractionCard key={index} interaction={interaction} />
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No drug interaction pairs were identified for this regimen.</p>
              )
            ) : (
              <p className="text-sm text-slate-500">Use the analyzer to reveal drug-drug interactions and severity levels.</p>
            )}
          </Card>

          <Card title="Contraindications and allergy conflicts">
            {assessment ? (
              <div className="space-y-4">
                {assessment.contraindications.length ? (
                  <div className="space-y-4">
                    {assessment.contraindications.map((item, index) => (
                      <WarningCard key={`contra-${index}`} title={`Contraindication: ${item.medication}`} details={item.explanation} recommendation={item.recommendation} severity={item.severity} />
                    ))}
                  </div>
                ) : null}
                {assessment.allergies.length ? (
                  <div className="space-y-4">
                    {assessment.allergies.map((item, index) => (
                      <WarningCard key={`allergy-${index}`} title={`Allergy conflict: ${item.medication}`} details={item.explanation} recommendation={item.recommendation} severity={item.severity} />
                    ))}
                  </div>
                ) : null}
                {!assessment.contraindications.length && !assessment.allergies.length ? (
                  <p className="text-sm text-slate-500">No contraindications or allergy conflicts were detected.</p>
                ) : null}
              </div>
            ) : null}
          </Card>

          <Card title="Clinical recommendations">
            {assessment ? (
              <DrugRecommendation assessment={assessment} />
            ) : (
              <p className="text-sm text-slate-500">A concise recommendation summary is available once the analysis completes.</p>
            )}
          </Card>
        </section>
      </div>
    </div>
  );
}
