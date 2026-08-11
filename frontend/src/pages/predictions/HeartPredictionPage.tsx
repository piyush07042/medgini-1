import PredictionPageShell, { type PredictionField } from "../../components/predictions/PredictionPageShell";
import { heartDiseaseSchema } from "../../utils/predictions";
import { predictHeartDisease } from "../../api/predictions";
import type { HeartDiseaseFormValues } from "../../types/form";
import type { HeartDiseasePredictionResponse, HeartDiseasePredictionRequest } from "../../types/api";

const defaultValues: HeartDiseaseFormValues = {
  age: 63,
  sex: 1,
  cp: 3,
  trestbps: 145,
  chol: 233,
  fbs: 1,
  restecg: 2,
  thalach: 150,
  exang: 0,
  oldpeak: 2.3,
  slope: 3,
  ca: 0,
  thal: 6,
};

const fields: Array<PredictionField<HeartDiseaseFormValues>> = [
  { name: "age", label: "Age", type: "number", placeholder: "63" },
  { name: "sex", label: "Sex (0=Female,1=Male)", type: "number", placeholder: "1" },
  { name: "cp", label: "Chest pain type", type: "number", placeholder: "3" },
  { name: "trestbps", label: "Resting blood pressure", type: "number", placeholder: "145" },
  { name: "chol", label: "Serum cholesterol", type: "number", placeholder: "233" },
  { name: "fbs", label: "Fasting blood sugar >120 mg/dl (0/1)", type: "number", placeholder: "1" },
  { name: "restecg", label: "Resting ECG result", type: "number", placeholder: "2" },
  { name: "thalach", label: "Max heart rate achieved", type: "number", placeholder: "150" },
  { name: "exang", label: "Exercise induced angina (0/1)", type: "number", placeholder: "0" },
  { name: "oldpeak", label: "ST depression", type: "number", placeholder: "2.3" },
  { name: "slope", label: "Slope of peak exercise ST segment", type: "number", placeholder: "3" },
  { name: "ca", label: "Number of major vessels colored by fluoroscopy", type: "number", placeholder: "0" },
  { name: "thal", label: "Thalassemia", type: "number", placeholder: "6" },
];

export default function HeartPredictionPage() {
  return (
    <PredictionPageShell<HeartDiseaseFormValues, HeartDiseasePredictionResponse>
      title="Heart Disease Prediction"
      description="Submit heart disease inputs exactly as the backend expects."
      schema={heartDiseaseSchema}
      defaultValues={defaultValues}
      fields={fields}
      predict={predictHeartDisease}
      successMessage="Heart disease prediction completed."
      submitLabel="Run prediction"
    />
  );
}
