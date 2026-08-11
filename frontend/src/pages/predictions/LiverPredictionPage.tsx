import PredictionPageShell, { type PredictionField } from "../../components/predictions/PredictionPageShell";
import { liverDiseaseSchema } from "../../utils/predictions";
import { predictLiverDisease } from "../../api/predictions";
import type { LiverDiseaseFormValues } from "../../types/form";
import type { LiverDiseasePredictionResponse } from "../../types/api";

const defaultValues: LiverDiseaseFormValues = {
  age: 55,
  bilirubin: 1.2,
  alk_phosphatase: 120.0,
  sgpt: 35.0,
  sgot: 40.0,
  name: "",
};

const fields: Array<PredictionField<LiverDiseaseFormValues>> = [
  { name: "age", label: "Age", type: "number", placeholder: "55" },
  { name: "bilirubin", label: "Bilirubin", type: "number", placeholder: "1.2" },
  { name: "alk_phosphatase", label: "Alkaline phosphatase", type: "number", placeholder: "120.0" },
  { name: "sgpt", label: "SGPT / ALT", type: "number", placeholder: "35.0" },
  { name: "sgot", label: "SGOT / AST", type: "number", placeholder: "40.0" },
  { name: "name", label: "Patient name", type: "text", placeholder: "Patient" },
];

export default function LiverPredictionPage() {
  return (
    <PredictionPageShell<LiverDiseaseFormValues, LiverDiseasePredictionResponse>
      title="Liver Disease Prediction"
      description="Submit liver disease inputs exactly as the backend expects."
      schema={liverDiseaseSchema}
      defaultValues={defaultValues}
      fields={fields}
      predict={predictLiverDisease}
      successMessage="Liver disease prediction completed."
    />
  );
}
