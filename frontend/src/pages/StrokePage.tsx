import PredictionPageShell, { type PredictionField } from "../components/predictions/PredictionPageShell";
import { strokeSchema } from "../utils/validation";
import { predictStroke } from "../api/stroke";
import type { StrokeFormValues } from "../types/form";
import type { StrokePredictionResponse } from "../types/api";

const defaultValues: StrokeFormValues = {
  age: 67,
  hypertension: 0,
  heart_disease: 0,
  avg_glucose_level: 140,
  bmi: 25,
  smoking_status: "formerly smoked",
  name: "",
};

const fields: Array<PredictionField<StrokeFormValues>> = [
  { name: "name", label: "Patient name", type: "text", placeholder: "John Doe" },
  { name: "age", label: "Age", type: "number", placeholder: "67" },
  { name: "hypertension", label: "Hypertension (0/1)", type: "number", placeholder: "1" },
  { name: "heart_disease", label: "Heart disease (0/1)", type: "number", placeholder: "1" },
  { name: "avg_glucose_level", label: "Avg glucose level", type: "number", placeholder: "228.69" },
  { name: "bmi", label: "BMI", type: "number", placeholder: "36.6" },
  { name: "smoking_status", label: "Smoking status", type: "text", placeholder: "formerly smoked" },
];

export default function StrokePage() {
  return (
    <PredictionPageShell<StrokeFormValues, StrokePredictionResponse>
      title="Stroke Risk Prediction"
      description="Evaluate stroke risk using clinical inputs and AI recommendations."
      schema={strokeSchema}
      defaultValues={defaultValues}
      fields={fields}
      predict={predictStroke}
      successMessage="Stroke risk prediction completed."
    />
  );
}
