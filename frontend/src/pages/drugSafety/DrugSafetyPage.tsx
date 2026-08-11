import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, ShieldCheck, AlertTriangle, ClipboardList, ArrowRight } from "lucide-react";
import PageHeading from "../../components/PageHeading";
import Card from "../../components/Card";
import FormField from "../../components/FormField";
import DrugSearch from "../../components/drugSafety/DrugSearch";
import DrugInteractionCard from "../../components/drugSafety/DrugInteractionCard";
import WarningCard from "../../components/drugSafety/WarningCard";
import AlternativeDrugCard from "../../components/drugSafety/AlternativeDrugCard";
import DrugHistory from "../../components/drugSafety/DrugHistory";
import DrugRecommendation from "../../components/drugSafety/DrugRecommendation";
import { analyzeDrugSafety, getDrugSafetyForPatient, storeDrugSafetyAssessment } from "../../api/drugSafety";
import { getPatientDetails } from "../../api/patients";
import type {
  DrugSafetyAssessmentResult,
  DrugSafetyStoredAssessment,
  Patient,
} from "../../types/api";

const DRUG_SUGGESTIONS = [
  "Aspirin",
  "Metformin",
  "Lisinopril",
  "Warfarin",
  "Ibuprofen",
  "Naproxen",
  "Spironolactone",
  "Ciprofloxacin",
  "Theophylline",
  "Prednisone",
  "Dexamethasone",
  "Acetaminophen",
  "Nitrofurantoin",
  "Gabapentin",
  "Statin",
  "Amiodarone",
  "Pseudoephedrine",
  "Propranolol",
  "Ketorolac",
  "Clarithromycin",
];

function formatDrugName(value: string) {
  return value
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase()
    .split(" ")
    .filter(Boolean)
    .map((item) => item[0].toUpperCase() + item.slice(1))
    .join(" ");
}

export default function DrugSafetyPage() {
  const [searchParams] = useSearchParams();
  const queryPatientId = searchParams.has("patientId") ? Number(searchParams.get("patientId")) : null;
  const patientId = queryPatientId !== null && Number.isInteger(queryPatientId) && queryPatientId > 0 ? queryPatientId : null;

  const [selectedMedications, setSelectedMedications] = useState<string[]>([]);
  const [allergies, setAllergies] = useState("");
  const [assessment, setAssessment] = useState<DrugSafetyAssessmentResult | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const queryClient = useQueryClient();

  const patientQuery = useQuery({
    queryKey: ["patientDetails", patientId],
    queryFn: () => (patientId ? getPatientDetails(patientId) : Promise.resolve(null)),
    enabled: Boolean(patientId),
    staleTime: 1000 * 60 * 5,
  });

  const historyQuery = useQuery({
    queryKey: ["drugSafetyHistory", patientId],
    queryFn: () => (patientId ? getDrugSafetyForPatient(patientId) : Promise.resolve({ success: false, message: "", data: [] })),
    enabled: Boolean(patientId),
    staleTime: 1000 * 60 * 5,
  });

  const patient = patientQuery.data as Patient | null;
  const history = (historyQuery.data?.data ?? []) as DrugSafetyStoredAssessment[];

  const hasSelectedMedications = selectedMedications.length > 0;

  const interactionCount = assessment?.interactions?.length ?? 0;
  const contraindicationCount = assessment?.contraindications?.length ?? 0;
  const allergyCount = assessment?.allergies?.length ?? 0;

  const summaryCards = useMemo(
    () => [
      {
        title: "Overall risk",
        value: assessment?.overall_risk ?? "Pending",
        icon: ShieldCheck,
        tone: assessment?.overall_risk === "High" ? "text-red-700 bg-red-50" : assessment?.overall_risk === "Medium" ? "text-amber-700 bg-amber-50" : "text-emerald-700 bg-emerald-50",
      },
      {
        title: "Interactions",
        value: String(interactionCount),
        icon: AlertTriangle,
        tone: "text-sky-700 bg-sky-50",
      },
      {
        title: "Warnings",
        value: String(contraindicationCount + allergyCount),
        icon: ClipboardList,
        tone: "text-violet-700 bg-violet-50",
      },
      {
        title: "Patient conditions",
        value: String(assessment?.patient_conditions?.length ?? 0),
        icon: ArrowRight,
        tone: "text-slate-700 bg-slate-100",
      },
    ],
    [assessment, interactionCount, contraindicationCount, allergyCount]
  );

  const handleAddMedication = (drug: string) => {
    const normalized = formatDrugName(drug);
    if (!normalized || selectedMedications.some((item) => item.toLowerCase() === normalized.toLowerCase())) {
      return;
    }
    setSelectedMedications((current) => [...current, normalized]);
  };

  const handleRemoveMedication = (drug: string) => {
    setSelectedMedications((current) => current.filter((item) => item.toLowerCase() !== drug.toLowerCase()));
  };

  const handleAnalyze = async () => {
    if (!hasSelectedMedications) {
      setAnalysisError("Select at least one medication before running the analysis.");
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

      const data = response.data?.drug_safety_assessment || response.data;
      if (!data) {
        throw new Error("Unexpected drug safety response from the server.");
      }

      setAssessment(data);
    } catch (error) {
      setAssessment(null);
      setAnalysisError("Unable to complete drug safety analysis. Check the entered medications and try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveAssessment = async () => {
    if (!patientId || !assessment || isSaving) return;

    setIsSaving(true);
    try {
      await storeDrugSafetyAssessment({
        patient_id: patientId,
        medications: selectedMedications,
        allergies: allergies
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      await queryClient.invalidateQueries({ queryKey: ["drugSafetyHistory", patientId] });
    } catch {
      // Fail silently, current UI remains usable.
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-10">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <PageHeading title="Drug Safety Center" description="Evaluate medication regimens, drug interactions, contraindications, and patient-specific safety warnings." />
        <Link
          to="/drug-safety/interactions"
          className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
        >
          View interaction checker
        </Link>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.3fr]">
        <section className="space-y-6">
          <Card title="Medication review">
            <div className="space-y-5">
              <DrugSearch
                selected={selectedMedications}
                onAdd={handleAddMedication}
                onRemove={handleRemoveMedication}
                suggestions={DRUG_SUGGESTIONS}
              />

              <FormField label="Patient allergies" placeholder="Penicillin, Sulfa" error={undefined} register={undefined}>
                <input
                  type="text"
                  value={allergies}
                  onChange={(event) => setAllergies(event.target.value)}
                  placeholder="Enter allergies separated by commas"
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-brand-400 focus:ring-4 focus:ring-brand-100"
                />
              </FormField>

              <div className="grid gap-3 sm:grid-cols-2">
                <button
                  type="button"
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                  className="rounded-2xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  {isAnalyzing ? "Analyzing medications..." : "Run drug safety review"}
                </button>
                <button
                  type="button"
                  onClick={handleSaveAssessment}
                  disabled={!patientId || !assessment || isSaving}
                  className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
                >
                  {patientId ? isSaving ? "Saving assessment…" : "Save patient assessment" : "Select a patient to save"}
                </button>
              </div>

              {patient ? (
                <div className="rounded-3xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm text-slate-500">Patient context</p>
                  <p className="mt-2 font-semibold text-slate-900">{patient.first_name} {patient.last_name}</p>
                  <p className="text-sm text-slate-600">Age {patient.age} · {patient.gender}</p>
                  <p className="mt-2 text-sm text-slate-500">Allergies: {patient.allergies?.join(", ") || "None recorded"}</p>
                </div>
              ) : null}

              {analysisError ? (
                <div className="rounded-3xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                  {analysisError}
                </div>
              ) : null}
            </div>
          </Card>

          <Card title="Patient history">
            {patientId ? (
              historyQuery.isLoading ? (
                <div className="space-y-3 py-4">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div key={index} className="h-14 rounded-3xl bg-slate-100" />
                  ))}
                </div>
              ) : history.length ? (
                <DrugHistory history={history} />
              ) : (
                <p className="text-sm text-slate-500">No previous drug safety records found for this patient.</p>
              )
            ) : (
              <p className="text-sm text-slate-500">Add a patient ID to the URL to load stored drug safety history for a selected patient.</p>
            )}
          </Card>
        </section>

        <section className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {summaryCards.map((card) => (
              <div key={card.title} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-soft">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-medium uppercase tracking-[0.24em] text-slate-400">{card.title}</p>
                    <p className="mt-3 text-3xl font-semibold text-slate-900">{card.value}</p>
                  </div>
                  <div className={`inline-flex h-12 w-12 items-center justify-center rounded-3xl ${card.tone}`}>
                    <card.icon className="h-5 w-5" />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <DrugRecommendation assessment={assessment} />

          <Card title="Key interactions and recommendations">
            {assessment ? (
              <div className="space-y-5">
                {assessment.interactions.length ? (
                  <div className="space-y-4">
                    <p className="text-sm font-semibold text-slate-900">Drug-drug interactions</p>
                    <div className="space-y-4">
                      {assessment.interactions.map((interaction, index) => (
                        <DrugInteractionCard key={index} interaction={interaction} />
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No significant drug-drug interactions were detected.</p>
                )}

                {assessment.contraindications.length ? (
                  <div className="space-y-4">
                    <p className="text-sm font-semibold text-slate-900">Contraindications</p>
                    <div className="space-y-4">
                      {assessment.contraindications.map((item, index) => (
                        <WarningCard key={index} title={`Contraindication: ${item.medication}`} details={item.explanation} recommendation={item.recommendation} severity={item.severity} />
                      ))}
                    </div>
                  </div>
                ) : null}

                {assessment.allergies.length ? (
                  <div className="space-y-4">
                    <p className="text-sm font-semibold text-slate-900">Allergy conflicts</p>
                    <div className="space-y-4">
                      {assessment.allergies.map((item, index) => (
                        <WarningCard key={index} title={`Allergy concern: ${item.medication}`} details={item.explanation} recommendation={item.recommendation} severity={item.severity} />
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Run an analysis to view interactions, contraindications, and allergy warnings.</p>
            )}
          </Card>

          <Card title="Clinical guidance">
            {assessment ? (
              <div className="space-y-4">
                <AlternativeDrugCard title="Pregnancy safety" summary={assessment.pregnancy.explanation} items={assessment.pregnancy.medications.map((item) => ({ label: item.medication, note: item.category }))} />
                <AlternativeDrugCard title="Renal dosing guidance" summary={assessment.renal_adjustment.monitoring_advice} items={assessment.renal_adjustment.recommendations.map((item) => ({ label: item.medication, note: item.recommendation }))} />
                <AlternativeDrugCard title="Liver dosing guidance" summary={assessment.liver_adjustment.monitoring_advice} items={assessment.liver_adjustment.recommendations.map((item) => ({ label: item.medication, note: item.recommendation }))} />
              </div>
            ) : (
              <p className="text-sm text-slate-500">A detailed safety summary will appear here after the review completes.</p>
            )}
          </Card>
        </section>
      </div>
    </div>
  );
}
