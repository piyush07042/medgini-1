import PredictionPageShell, { type PredictionField } from "../../components/predictions/PredictionPageShell";
import { parkinsonsSchema } from "../../utils/predictions";
import { predictParkinsons } from "../../api/predictions";
import type { ParkinsonsFormValues } from "../../types/form";
import type { ParkinsonsPredictionResponse } from "../../types/api";

const defaultValues: ParkinsonsFormValues = {
  age: 65,
  motor_UPDRS: 28.0,
  total_UPDRS: 34.0,
  Jitter_local: 0.005,
  Shimmer_local: 0.03,
  name: "",
};

const fields: Array<PredictionField<ParkinsonsFormValues>> = [
  { name: "age", label: "Age (years)", type: "number", placeholder: "65" },
  { name: "motor_UPDRS", label: "Motor UPDRS Score", type: "number", placeholder: "28.0", step: "0.1" },
  { name: "total_UPDRS", label: "Total UPDRS Score", type: "number", placeholder: "34.0", step: "0.1" },
  { name: "Jitter_local", label: "Jitter Local (%)", type: "number", placeholder: "0.005", step: "0.001" },
  { name: "Shimmer_local", label: "Shimmer Local", type: "number", placeholder: "0.03", step: "0.001" },
  { name: "name", label: "Patient Name", type: "text", placeholder: "Patient" },
];

export default function ParkinsonPredictionPage() {
  return (
    <PredictionPageShell<ParkinsonsFormValues, ParkinsonsPredictionResponse>
      title="Parkinson's Disease Prediction"
      description="Submit Parkinson's disease inputs exactly as the backend expects."
      schema={parkinsonsSchema}
      defaultValues={defaultValues}
      fields={fields}
      predict={predictParkinsons}
      successMessage="Parkinson's disease prediction completed."
    />
  );
}
