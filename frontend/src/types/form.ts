export type LoginFormValues = {
  email: string;
  password: string;
};

export type RegisterFormValues = {
  email: string;
  password: string;
  full_name: string;
};

export type PatientFormValues = {
  first_name: string;
  last_name: string;
  age: number;
  gender: string;
  allergies: string;
  current_medications: string;
  medical_history: string;
};

export type StrokeFormValues = {
  age: number;
  hypertension: number;
  heart_disease: number;
  avg_glucose_level: number;
  bmi: number;
  smoking_status: string;
  name?: string;
};

export type HeartDiseaseFormValues = {
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

export type DiabetesFormValues = {
  age: number;
  bmi: number;
  glucose: number;
  systolic_bp: number;
  insulin: number;
  name?: string;
};

export type KidneyDiseaseFormValues = {
  age: number;
  creatinine: number;
  blood_urea: number;
  sgpt: number;
  albumin: number;
  name?: string;
};

export type LiverDiseaseFormValues = {
  age: number;
  bilirubin: number;
  alk_phosphatase: number;
  sgpt: number;
  sgot: number;
  name?: string;
};

export type BreastCancerFormValues = {
  radius_mean: number;
  texture_mean: number;
  perimeter_mean: number;
  area_mean: number;
  smoothness_mean: number;
  name?: string;
};

export type ParkinsonsFormValues = {
  age: number;
  motor_UPDRS: number;
  total_UPDRS: number;
  Jitter_local: number;
  Shimmer_local: number;
  name?: string;
};

export type HepatitisFormValues = {
  age: number;
  bilirubin: number;
  alk_phosphatase: number;
  sgpt: number;
  sgot: number;
  name?: string;
};

export type HeartFailureFormValues = {
  age: number;
  ejection_fraction: number;
  serum_creatinine: number;
  serum_sodium: number;
  time: number;
  name?: string;
};

export type DrugSafetyFormValues = {
  medications: string;
  allergies: string;
};

export type ChatFormValues = {
  message: string;
};
