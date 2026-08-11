export type ApiResponse<T> = {
  success: boolean;
  message: string;
  data: T | null;
};

export type AuthToken = {
  access_token: string;
  token_type: string;
  user: User;
};

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  avatar_url?: string | null;
  created_at: string;
};

export type Patient = {
  id: number;
  doctor_id: number;
  first_name: string;
  last_name: string;
  age: number;
  gender: string;
  medical_history?: Record<string, any>;
  allergies?: string[];
  current_medications?: string[];
  avatar_url?: string | null;
  created_at: string;
};

export type PatientTimelineEvent = {
  id: string;
  title: string;
  description: string;
  event_type: string;
  date: string;
  source: string;
};

export type PatientVisitRecord = {
  id: string;
  date: string;
  visit_type: string;
  summary: string;
  status: string;
};

export type HeartDiseasePredictionRequest = {
  age: number;
  sex: number;
  cp: number;
  trestbps: number;
  chol: number;
  fbs: number;
  restecg: number;
  thalach: number;
  exang: number;
  oldpeak: number;
  slope: number;
  ca: number;
  thal: number;
};

export type HeartDiseasePredictionResponse = {
  success: boolean;
  disease: string;
  prediction: number;
  probability: number;
  confidence: number;
  confidence_label: string | null;
  explanations?: Array<Record<string, any>>;
  recommendations?: Array<Record<string, any>>;
  structured_recommendation?: Record<string, any> | null;
  final_report?: Record<string, any> | null;
  evidence?: Array<Record<string, any>> | null;
  citations?: Array<Record<string, any>> | null;
  similarity_scores?: number[] | null;
  evidence_summary?: string | null;
  class_probabilities: Record<string, number>;
  drug_safety?: Record<string, any> | null;
};

export type DiabetesPredictionRequest = {
  age: number;
  bmi: number;
  glucose: number;
  systolic_bp: number;
  insulin: number;
  name?: string | null;
};

export type DiabetesPredictionResponse = {
  success: boolean;
  disease: string;
  prediction: number;
  probability: number;
  confidence: number;
  confidence_label: string | null;
  explanations?: Array<Record<string, any>>;
  recommendations?: Array<Record<string, any>>;
  structured_recommendation?: Record<string, any> | null;
  final_report?: Record<string, any> | null;
  evidence?: Array<Record<string, any>> | null;
  citations?: Array<Record<string, any>> | null;
  similarity_scores?: number[] | null;
  evidence_summary?: string | null;
  class_probabilities: Record<string, number>;
  drug_safety?: Record<string, any> | null;
};

export type ReportTemplateResponse = {
  templates: string[];
};

export type KidneyDiseasePredictionRequest = {
  age: number;
  creatinine: number;
  blood_urea: number;
  sgpt: number;
  albumin: number;
  name?: string | null;
};

export type KidneyDiseasePredictionResponse = {
  success: boolean;
  disease: string;
  prediction: number;
  probability: number;
  confidence: number;
  confidence_label: string | null;
  explanations?: Array<Record<string, any>>;
  recommendations?: Array<Record<string, any>>;
  structured_recommendation?: Record<string, any> | null;
  final_report?: Record<string, any> | null;
  evidence?: Array<Record<string, any>> | null;
  citations?: Array<Record<string, any>> | null;
  similarity_scores?: number[] | null;
  evidence_summary?: string | null;
  class_probabilities: Record<string, number>;
  drug_safety?: Record<string, any> | null;
};

export type LiverDiseasePredictionRequest = {
  age: number;
  bilirubin: number;
  alk_phosphatase: number;
  sgpt: number;
  sgot: number;
  name?: string | null;
};

export type LiverDiseasePredictionResponse = {
  success: boolean;
  disease: string;
  prediction: number;
  probability: number;
  confidence: number;
  confidence_label: string | null;
  explanations?: Array<Record<string, any>>;
  recommendations?: Array<Record<string, any>>;
  structured_recommendation?: Record<string, any> | null;
  final_report?: Record<string, any> | null;
  evidence?: Array<Record<string, any>> | null;
  citations?: Array<Record<string, any>> | null;
  similarity_scores?: number[] | null;
  evidence_summary?: string | null;
  class_probabilities: Record<string, number>;
  drug_safety?: Record<string, any> | null;
};

export type BreastCancerPredictionRequest = {
  radius_mean: number;
  texture_mean: number;
  perimeter_mean: number;
  area_mean: number;
  smoothness_mean: number;
  name?: string | null;
};

export type BreastCancerPredictionResponse = {
  success: boolean;
  disease: string;
  prediction: number;
  probability: number;
  confidence: number;
  confidence_label: string | null;
  explanations?: Array<Record<string, any>>;
  recommendations?: Array<Record<string, any>>;
  structured_recommendation?: Record<string, any> | null;
  final_report?: Record<string, any> | null;
  evidence?: Array<Record<string, any>> | null;
  citations?: Array<Record<string, any>> | null;
  similarity_scores?: number[] | null;
  evidence_summary?: string | null;
  class_probabilities: Record<string, number>;
  drug_safety?: Record<string, any> | null;
};

export type ParkinsonsPredictionRequest = {
  age: number;
  motor_UPDRS: number;
  total_UPDRS: number;
  Jitter_local: number;
  Shimmer_local: number;
  name?: string | null;
};

export type ParkinsonsPredictionResponse = {
  success: boolean;
  disease: string;
  prediction: number;
  probability: number;
  confidence: number;
  confidence_label: string | null;
  explanations?: Array<Record<string, any>>;
  recommendations?: Array<Record<string, any>>;
  structured_recommendation?: Record<string, any> | null;
  final_report?: Record<string, any> | null;
  evidence?: Array<Record<string, any>> | null;
  citations?: Array<Record<string, any>> | null;
  similarity_scores?: number[] | null;
  evidence_summary?: string | null;
  class_probabilities: Record<string, number>;
  drug_safety?: Record<string, any> | null;
};

export type HepatitisPredictionRequest = {
  age: number;
  bilirubin: number;
  alk_phosphatase: number;
  sgpt: number;
  sgot: number;
  name?: string | null;
};

export type HepatitisPredictionResponse = {
  success: boolean;
  disease: string;
  prediction: number;
  probability: number;
  confidence: number;
  confidence_label: string | null;
  explanations?: Array<Record<string, any>>;
  recommendations?: Array<Record<string, any>>;
  structured_recommendation?: Record<string, any> | null;
  final_report?: Record<string, any> | null;
  evidence?: Array<Record<string, any>> | null;
  citations?: Array<Record<string, any>> | null;
  similarity_scores?: number[] | null;
  evidence_summary?: string | null;
  class_probabilities: Record<string, number> | Record<string, any>;
  drug_safety?: Record<string, any> | null;
};

export type HeartFailurePredictionRequest = {
  age: number;
  ejection_fraction: number;
  serum_creatinine: number;
  serum_sodium: number;
  time: number;
  name?: string | null;
};

export type HeartFailurePredictionResponse = {
  success: boolean;
  disease: string;
  prediction: number;
  probability: number;
  confidence: number;
  confidence_label: string | null;
  explanations?: Array<Record<string, any>>;
  recommendations?: Array<Record<string, any>>;
  structured_recommendation?: Record<string, any> | null;
  final_report?: Record<string, any> | null;
  evidence?: Array<Record<string, any>> | null;
  citations?: Array<Record<string, any>> | null;
  similarity_scores?: number[] | null;
  evidence_summary?: string | null;
  class_probabilities: Record<string, number>;
  drug_safety?: Record<string, any> | null;
};

export type StrokePredictionRequest = {
  age?: number;
  hypertension?: number;
  heart_disease?: number;
  avg_glucose_level?: number;
  bmi?: number;
  smoking_status?: string;
  name?: string;
};

export type StrokePredictionResponse = {
  success: boolean;
  disease: string;
  prediction: number;
  probability: number;
  confidence: number;
  confidence_label: string;
  class_probabilities: Record<string, number>;
  explanations: Array<Record<string, any>>;
  fallback_reason?: string;
  recommendations?: Array<Record<string, any>>;
  report?: Record<string, any>;
};

export type HealthStatus = {
  status: string;
  service: string;
  model_loaded?: boolean;
  model_directory?: string;
};

export type WorkflowState = {
  patient?: Record<string, any>;
  patient_summary?: Record<string, any>;
  patient_history?: Record<string, any>;
  symptoms?: string[];
  medications?: string[];
  allergies?: string[];
  uploaded_reports?: string[];
  report_text?: string;
  ocr_result?: Record<string, any>;
  extracted_metrics?: Record<string, any>;
  disease_risk?: Record<string, any>;
  knowledge_results?: Array<Record<string, any>>;
  drug_analysis?: Record<string, any>;
  recommendations?: Array<Record<string, any>>;
  final_report?: Record<string, any>;
  metadata?: Record<string, any>;
  warnings?: string[];
  errors?: string[];
};

export type UploadReportResponse = {
  workflow_state?: WorkflowState;
  agent_results?: Array<Record<string, any>>;
  workflow_metrics?: Record<string, any>;
};

export type DrugSafetyAssessmentResult = {
  status: string;
  overall_risk: string;
  medications_checked: string[];
  interactions: Array<{
    drugs_involved: string[];
    severity: string;
    explanation: string;
    recommendation: string;
  }>;
  contraindications: Array<{
    medication: string;
    condition: string;
    severity: string;
    explanation: string;
    recommendation: string;
  }>;
  allergies: Array<{
    medication: string;
    allergy_type: string;
    severity: string;
    explanation: string;
    recommendation: string;
  }>;
  pregnancy: {
    category: string;
    explanation: string;
    medications: Array<{ medication: string; category: string; explanation: string }>;
  };
  renal_adjustment: {
    egfr?: number | null;
    creatinine?: number | null;
    ckd_stage?: number | null;
    recommendations: Array<{ medication: string; recommendation: string; avoid_drug: boolean }>;
    avoid_drugs: string[];
    monitoring_advice: string;
  };
  liver_adjustment: {
    alt?: number | null;
    ast?: number | null;
    bilirubin?: number | null;
    recommendations: Array<{ medication: string; recommendation: string; avoid_drug: boolean }>;
    avoid_drugs: string[];
    monitoring_advice: string;
  };
  patient_conditions: string[];
  recommendation: string;
};

export type DrugSafetyStoredAssessment = {
  id: number;
  created_at: string;
  assessment: {
    drug_safety_assessment: DrugSafetyAssessmentResult;
  };
};

export type UploadHistoryItem = {
  id: string;
  filename: string;
  fileType: string;
  uploadedAt: string;
  status: "completed" | "failed";
  patientName?: string;
  prediction?: string;
  riskLevel?: string;
  confidence?: number;
  summary?: string;
  workflowState?: WorkflowState;
};
