import PredictionPageShell, { type PredictionField } from "../../components/predictions/PredictionPageShell";
import { diabetesSchema } from "../../utils/predictions";
import { predictDiabetes } from "../../api/predictions";
import type { DiabetesFormValues } from "../../types/form";
import type { DiabetesPredictionResponse } from "../../types/api";

const defaultValues: DiabetesFormValues = {
  age: 55,
  bmi: 28.5,
  glucose: 120,
  systolic_bp: 80,
  insulin: 79,
  name: "",
};

const fields: Array<PredictionField<DiabetesFormValues>> = [
  { name: "age", label: "Age (years)", type: "number", placeholder: "55" },
  { name: "bmi", label: "BMI", type: "number", placeholder: "28.5", step: "0.1" },
  { name: "glucose", label: "Glucose Level (mg/dL)", type: "number", placeholder: "120" },
  { name: "systolic_bp", label: "Systolic Blood Pressure (mm Hg)", type: "number", placeholder: "80" },
  { name: "insulin", label: "Insulin (µU/ml)", type: "number", placeholder: "79" },
  { name: "name", label: "Patient Name", type: "text", placeholder: "Patient" },
];

export default function DiabetesPredictionPage() {
  return (
    <PredictionPageShell<DiabetesFormValues, DiabetesPredictionResponse>
      title="Diabetes Readmission Risk"
      description="Submit patient inputs to predict hospital readmission risk."
      schema={diabetesSchema}
      defaultValues={defaultValues}
      fields={fields}
      predict={predictDiabetes}
      successMessage="Diabetes readmission risk prediction completed."
    />
  );
}
