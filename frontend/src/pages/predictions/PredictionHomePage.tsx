import { Heart, Activity, Droplet, Ribbon, BrainCog, Pill, HeartPulse, ShieldCheck } from "lucide-react";
import { useLocation } from "react-router-dom";
import DiseaseCard from "../../components/predictions/DiseaseCard";
import PageHeading from "../../components/PageHeading";

const predictions = [
  {
    title: "Heart Disease",
    icon: Heart,
    description: "Run cardiac risk prediction using standard heart disease measurements.",
    inputs: ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"],
    to: "/heart-disease",
  },
  {
    title: "Diabetes",
    icon: Droplet,
    description: "Assess diabetes risk with BMI, glucose, blood pressure and insulin values.",
    inputs: ["age", "bmi", "glucose", "systolic_bp", "insulin"],
    to: "/diabetes",
  },
  {
    title: "Chronic Kidney Disease",
    icon: Activity,
    description: "Evaluate kidney disease risk using creatinine, blood urea and albumin.",
    inputs: ["age", "creatinine", "blood_urea", "sgpt", "albumin"],
    to: "/kidney-disease",
  },
  {
    title: "Liver Disease",
    icon: HeartPulse,
    description: "Detect liver pathology from bilirubin, enzymes and liver biomarkers.",
    inputs: ["age", "bilirubin", "alk_phosphatase", "sgpt", "sgot"],
    to: "/liver-disease",
  },
  {
    title: "Breast Cancer",
    icon: Ribbon,
    description: "Predict breast cancer using tumor shape and texture measurements.",
    inputs: ["radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean"],
    to: "/breast-cancer",
  },
  {
    title: "Parkinson's Disease",
    icon: BrainCog,
    description: "Assess Parkinson's risk with motor ratings and voice biomarkers.",
    inputs: ["age", "motor_UPDRS", "total_UPDRS", "Jitter_local", "Shimmer_local"],
    to: "/parkinsons",
  },
  {
    title: "Hepatitis",
    icon: Pill,
    description: "Screen hepatitis risk from liver function biomarkers.",
    inputs: ["age", "bilirubin", "alk_phosphatase", "sgpt", "sgot"],
    to: "/hepatitis",
  },
  {
    title: "Heart Failure",
    icon: ShieldCheck,
    description: "Estimate heart failure risk using ejection fraction and lab values.",
    inputs: ["age", "ejection_fraction", "serum_creatinine", "serum_sodium", "time"],
    to: "/heart-failure",
  },
  {
    title: "Stroke",
    icon: BrainCog,
    description: "Predict stroke risk based on hypertension, glucose and cardiovascular inputs.",
    inputs: ["age", "hypertension", "heart_disease", "avg_glucose_level", "bmi", "smoking_status"],
    to: "/stroke",
  },
];

export default function PredictionHomePage() {
  const location = useLocation();

  return (
    <div className="space-y-10">
      <PageHeading title="Disease Prediction Center" description="Choose a model and run a clinical prediction using your patient data." />
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {predictions.map((prediction) => (
          <DiseaseCard key={prediction.title} {...prediction} state={location.state} />
        ))}
      </div>
    </div>
  );
}
