import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(6, "Password must be at least 6 characters."),
});

export const registerSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(6, "Password must be at least 6 characters."),
  full_name: z.string().min(2, "Enter your full name."),
});

export const patientSchema = z.object({
  first_name: z.string().min(2, "Enter a first name."),
  last_name: z.string().min(2, "Enter a last name."),
  age: z.coerce.number().min(0, "Enter a valid age."),
  gender: z.string().min(2, "Select a gender."),
  allergies: z.string().optional(),
  current_medications: z.string().optional(),
  medical_history: z.string().optional(),
});

export const strokeSchema = z.object({
  age: z.coerce.number().min(0, "Enter a valid age."),
  hypertension: z.coerce.number().min(0, "Enter 0 or 1.").max(1, "Enter 0 or 1."),
  heart_disease: z.coerce.number().min(0, "Enter 0 or 1.").max(1, "Enter 0 or 1."),
  avg_glucose_level: z.coerce.number().min(0, "Enter a valid glucose level."),
  bmi: z.coerce.number().min(0, "Enter a valid BMI."),
  smoking_status: z.string().min(2, "Enter smoking status."),
  name: z.string().optional(),
});

export const drugSafetySchema = z.object({
  medications: z.string().min(3, "Enter at least one medication."),
  allergies: z.string().optional(),
});

export const chatSchema = z.object({
  message: z.string().min(3, "Tell us what you need.").max(500, "Message is too long."),
});
