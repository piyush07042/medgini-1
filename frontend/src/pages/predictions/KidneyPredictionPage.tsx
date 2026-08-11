import PredictionPageShell, { type PredictionField } from "../../components/predictions/PredictionPageShell";
import { kidneyDiseaseSchema } from "../../utils/predictions";
import { predictKidneyDisease } from "../../api/predictions";
import type { KidneyDiseaseFormValues } from "../../types/form";
import type { KidneyDiseasePredictionResponse } from "../../types/api";

const defaultValues: KidneyDiseaseFormValues = {
  age: 55,
  creatinine: 1.2,
  blood_urea: 30.0,
  sgpt: 25.0,
  albumin: 4.2,
  name: "",
};

const fields: Array<PredictionField<KidneyDiseaseFormValues>> = [
  { name: "age", label: "Age (years)", type: "number", placeholder: "55" },
  { name: "creatinine", label: "Serum Creatinine (mg/dL)", type: "number", placeholder: "1.2", step: "0.1" },
  { name: "blood_urea", label: "Blood Urea (mg/dL)", type: "number", placeholder: "30.0", step: "0.1" },
  { name: "sgpt", label: "SGPT (U/L)", type: "number", placeholder: "25.0", step: "0.1" },
  { name: "albumin", label: "Serum Albumin (g/dL)", type: "number", placeholder: "4.2", step: "0.1" },
  { name: "name", label: "Patient Name", type: "text", placeholder: "Patient" },
];

export default function KidneyPredictionPage() {
  return (
    <PredictionPageShell<KidneyDiseaseFormValues, KidneyDiseasePredictionResponse>
      title="Chronic Kidney Disease Prediction"
      description="Submit kidney disease inputs exactly as the backend expects."
      schema={kidneyDiseaseSchema}
      defaultValues={defaultValues}
      fields={fields}
      predict={predictKidneyDisease}
      successMessage="Kidney disease prediction completed."
    />
  );
}
