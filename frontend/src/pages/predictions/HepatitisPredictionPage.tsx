import PredictionPageShell, { type PredictionField } from "../../components/predictions/PredictionPageShell";
import { hepatitisSchema } from "../../utils/predictions";
import { predictHepatitis } from "../../api/predictions";
import type { HepatitisFormValues } from "../../types/form";
import type { HepatitisPredictionResponse } from "../../types/api";

const defaultValues: HepatitisFormValues = {
  age: 55,
  bilirubin: 1.0,
  alk_phosphatase: 200.0,
  sgpt: 40.0,
  sgot: 35.0,
  name: "",
};

const fields: Array<PredictionField<HepatitisFormValues>> = [
  { name: "age", label: "Age", type: "number", placeholder: "55" },
  { name: "bilirubin", label: "Bilirubin", type: "number", placeholder: "1.0" },
  { name: "alk_phosphatase", label: "Alkaline phosphatase", type: "number", placeholder: "200.0" },
  { name: "sgpt", label: "SGPT / ALT", type: "number", placeholder: "40.0" },
  { name: "sgot", label: "SGOT / AST", type: "number", placeholder: "35.0" },
  { name: "name", label: "Patient name", type: "text", placeholder: "Patient" },
];

export default function HepatitisPredictionPage() {
  return (
    <PredictionPageShell<HepatitisFormValues, HepatitisPredictionResponse>
      title="Hepatitis Prediction"
      description="Submit hepatitis blood panel values exactly as the backend expects."
      schema={hepatitisSchema}
      defaultValues={defaultValues}
      fields={fields}
      predict={predictHepatitis}
      successMessage="Hepatitis prediction completed."
    />
  );
}
