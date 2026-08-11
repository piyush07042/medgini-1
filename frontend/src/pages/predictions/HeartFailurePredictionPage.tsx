import PredictionPageShell, { type PredictionField } from "../../components/predictions/PredictionPageShell";
import { heartFailureSchema } from "../../utils/predictions";
import { predictHeartFailure } from "../../api/predictions";
import type { HeartFailureFormValues } from "../../types/form";
import type { HeartFailurePredictionResponse } from "../../types/api";

const defaultValues: HeartFailureFormValues = {
  age: 60,
  ejection_fraction: 35,
  serum_creatinine: 1.1,
  serum_sodium: 135,
  time: 4,
  name: "",
};

const fields: Array<PredictionField<HeartFailureFormValues>> = [
  { name: "age", label: "Age", type: "number", placeholder: "60" },
  { name: "ejection_fraction", label: "Ejection fraction", type: "number", placeholder: "35" },
  { name: "serum_creatinine", label: "Serum creatinine", type: "number", placeholder: "1.1" },
  { name: "serum_sodium", label: "Serum sodium", type: "number", placeholder: "135" },
  { name: "time", label: "Time", type: "number", placeholder: "4" },
  { name: "name", label: "Patient name", type: "text", placeholder: "Patient" },
];

export default function HeartFailurePredictionPage() {
  return (
    <PredictionPageShell<HeartFailureFormValues, HeartFailurePredictionResponse>
      title="Heart Failure Prediction"
      description="Submit heart failure risk factors exactly as the backend expects."
      schema={heartFailureSchema}
      defaultValues={defaultValues}
      fields={fields}
      predict={predictHeartFailure}
      successMessage="Heart failure prediction completed."
    />
  );
}
