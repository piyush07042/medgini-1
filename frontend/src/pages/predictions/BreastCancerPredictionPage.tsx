import PredictionPageShell, { type PredictionField } from "../../components/predictions/PredictionPageShell";
import { breastCancerSchema } from "../../utils/predictions";
import { predictBreastCancer } from "../../api/predictions";
import type { BreastCancerFormValues } from "../../types/form";
import type { BreastCancerPredictionResponse } from "../../types/api";

const defaultValues: BreastCancerFormValues = {
  radius_mean: 17.99,
  texture_mean: 10.38,
  perimeter_mean: 122.8,
  area_mean: 1001.0,
  smoothness_mean: 0.1184,
  name: "",
};

const fields: Array<PredictionField<BreastCancerFormValues>> = [
  { name: "radius_mean", label: "Radius mean", type: "number", placeholder: "17.99" },
  { name: "texture_mean", label: "Texture mean", type: "number", placeholder: "10.38" },
  { name: "perimeter_mean", label: "Perimeter mean", type: "number", placeholder: "122.8" },
  { name: "area_mean", label: "Area mean", type: "number", placeholder: "1001.0" },
  { name: "smoothness_mean", label: "Smoothness mean", type: "number", placeholder: "0.1184" },
  { name: "name", label: "Patient name", type: "text", placeholder: "Patient" },
];

export default function BreastCancerPredictionPage() {
  return (
    <PredictionPageShell<BreastCancerFormValues, BreastCancerPredictionResponse>
      title="Breast Cancer Prediction"
      description="Submit breast cancer tumor metrics exactly as the backend expects."
      schema={breastCancerSchema}
      defaultValues={defaultValues}
      fields={fields}
      predict={predictBreastCancer}
      successMessage="Breast cancer prediction completed."
    />
  );
}
