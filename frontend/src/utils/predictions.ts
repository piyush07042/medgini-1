import { z } from "zod";

export const heartDiseaseSchema = z.object({
  age: z.coerce.number().min(1, "Enter a valid age.").max(120, "Age must be 120 or lower."),
  sex: z.coerce.number().min(0, "Enter 0 or 1.").max(1, "Enter 0 or 1."),
  cp: z.coerce.number().min(1, "Enter a chest pain type between 1-4.").max(4, "Enter a chest pain type between 1-4."),
  trestbps: z.coerce.number().min(50, "Enter a valid resting blood pressure.").max(300, "Enter a valid resting blood pressure."),
  chol: z.coerce.number().min(50, "Enter a valid cholesterol value.").max(700, "Enter a valid cholesterol value."),
  fbs: z.coerce.number().min(0, "Enter 0 or 1.").max(1, "Enter 0 or 1."),
  restecg: z.coerce.number().min(0, "Enter 0-2.").max(2, "Enter 0-2."),
  thalach: z.coerce.number().min(50, "Enter a valid maximum heart rate.").max(250, "Enter a valid maximum heart rate."),
  exang: z.coerce.number().min(0, "Enter 0 or 1.").max(1, "Enter 0 or 1."),
  oldpeak: z.coerce.number().min(0, "Enter a valid ST depression value.").max(10, "Enter a valid ST depression value."),
  slope: z.coerce.number().min(1, "Enter 1-3.").max(3, "Enter 1-3."),
  ca: z.coerce.number().min(0, "Enter 0-4.").max(4, "Enter 0-4."),
  thal: z.coerce.number().min(3, "Enter 3-7.").max(7, "Enter 3-7."),
});

export const diabetesSchema = z.object({
  age: z.coerce.number().min(1, "Enter a valid age.").max(120, "Age must be 120 or lower."),
  bmi: z.coerce.number().min(10, "Enter a valid BMI.").max(80, "Enter a valid BMI."),
  glucose: z.coerce.number().min(50, "Enter a valid glucose value.").max(400, "Enter a valid glucose value."),
  systolic_bp: z.coerce.number().min(50, "Enter a valid systolic BP.").max(250, "Enter a valid systolic BP."),
  insulin: z.coerce.number().min(0, "Enter a valid insulin level.").max(1000, "Enter a valid insulin level."),
  name: z.string().optional(),
});

export const kidneyDiseaseSchema = z.object({
  age: z.coerce.number().min(1, "Enter a valid age.").max(120, "Age must be 120 or lower."),
  creatinine: z.coerce.number().min(0.1, "Enter a valid creatinine value.").max(50, "Enter a valid creatinine value."),
  blood_urea: z.coerce.number().min(0, "Enter a valid blood urea value.").max(300, "Enter a valid blood urea value."),
  sgpt: z.coerce.number().min(0, "Enter a valid SGPT.").max(300, "Enter a valid SGPT."),
  albumin: z.coerce.number().min(0, "Enter a valid albumin value.").max(10, "Enter a valid albumin value."),
  name: z.string().optional(),
});

export const liverDiseaseSchema = z.object({
  age: z.coerce.number().min(1, "Enter a valid age.").max(120, "Age must be 120 or lower."),
  bilirubin: z.coerce.number().min(0, "Enter a valid bilirubin value.").max(50, "Enter a valid bilirubin value."),
  alk_phosphatase: z.coerce.number().min(0, "Enter a valid alkaline phosphatase value.").max(1000, "Enter a valid alkaline phosphatase value."),
  sgpt: z.coerce.number().min(0, "Enter a valid SGPT.").max(1000, "Enter a valid SGPT."),
  sgot: z.coerce.number().min(0, "Enter a valid SGOT.").max(1000, "Enter a valid SGOT."),
  name: z.string().optional(),
});

export const breastCancerSchema = z.object({
  radius_mean: z.coerce.number().min(0, "Enter a valid radius mean.").max(100, "Enter a valid radius mean."),
  texture_mean: z.coerce.number().min(0, "Enter a valid texture mean.").max(100, "Enter a valid texture mean."),
  perimeter_mean: z.coerce.number().min(0, "Enter a valid perimeter mean.").max(300, "Enter a valid perimeter mean."),
  area_mean: z.coerce.number().min(0, "Enter a valid area mean.").max(2500, "Enter a valid area mean."),
  smoothness_mean: z.coerce.number().min(0, "Enter a valid smoothness mean.").max(1, "Enter a valid smoothness mean."),
  name: z.string().optional(),
});

export const parkinsonsSchema = z.object({
  age: z.coerce.number().min(1, "Enter a valid age.").max(120, "Age must be 120 or lower."),
  motor_UPDRS: z.coerce.number().min(0, "Enter a valid Motor UPDRS value.").max(100, "Enter a valid Motor UPDRS value."),
  total_UPDRS: z.coerce.number().min(0, "Enter a valid Total UPDRS value.").max(200, "Enter a valid Total UPDRS value."),
  Jitter_local: z.coerce.number().min(0, "Enter a valid Jitter local value.").max(0.1, "Enter a valid Jitter local value."),
  Shimmer_local: z.coerce.number().min(0, "Enter a valid Shimmer local value.").max(0.2, "Enter a valid Shimmer local value."),
  name: z.string().optional(),
});

export const hepatitisSchema = z.object({
  age: z.coerce.number().min(0, "Enter a valid age."),
  bilirubin: z.coerce.number().min(0, "Enter a valid bilirubin value."),
  alk_phosphatase: z.coerce.number().min(0, "Enter a valid alkaline phosphatase value."),
  sgpt: z.coerce.number().min(0, "Enter a valid SGPT value."),
  sgot: z.coerce.number().min(0, "Enter a valid SGOT value."),
  name: z.string().optional(),
});

export const heartFailureSchema = z.object({
  age: z.coerce.number().min(1, "Enter a valid age.").max(120, "Age must be 120 or lower."),
  ejection_fraction: z.coerce.number().min(5, "Enter a valid ejection fraction.").max(80, "Enter a valid ejection fraction."),
  serum_creatinine: z.coerce.number().min(0.2, "Enter a valid serum creatinine.").max(10, "Enter a valid serum creatinine."),
  serum_sodium: z.coerce.number().min(100, "Enter a valid serum sodium value.").max(150, "Enter a valid serum sodium value."),
  time: z.coerce.number().min(0, "Enter a valid follow-up time.").max(500, "Enter a valid follow-up time."),
  name: z.string().optional(),
});
