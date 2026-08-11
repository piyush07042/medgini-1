import { findGuidelinesForDisease, GuidelineEntry } from "../utils/clinicalGuidelines";

export type RecommendationOutput = {
  interpretation: string;
  guideline_references: GuidelineEntry[];
  recommendations: string[];
  lifestyle_advice: string[];
  follow_up_plan: { when: string; action: string }[];
  monitoring_schedule: { measure: string; frequency: string }[];
  emergency_warning_signs: string[];
};

export function generateRecommendations(params: {
  disease?: string | null;
  prediction?: number | boolean | null;
  probability?: number | null;
  risk_label?: string | null;
  patient?: Record<string, any> | null;
}): RecommendationOutput {
  const { disease, prediction, probability, risk_label, patient } = params;
  const prob = typeof probability === "number" ? probability : Number(probability) || 0;
  const guidelines = findGuidelinesForDisease(disease);

  // Determine severity
  const high = prob >= 0.65 || String(risk_label ?? "").toLowerCase().includes("high") || Number(prediction) === 1;
  const moderate = !high && prob >= 0.4;

  const interpretation = high
    ? `High-risk assessment for ${disease ?? "the condition"}.` 
    : moderate
    ? `Moderate risk for ${disease ?? "the condition"}.` 
    : `Low risk for ${disease ?? "the condition"}.`;

  // Base recommendations: use guideline bullets for high risk; otherwise suggest monitoring/lifestyle
  const recommendations: string[] = [];
  const lifestyle_advice: string[] = [];
  const follow_up_plan: { when: string; action: string }[] = [];
  const monitoring_schedule: { measure: string; frequency: string }[] = [];
  const emergency_warning_signs: string[] = [];

  if (guidelines && guidelines.length) {
    if (high) {
      // use primary bullets from guidelines
      guidelines.forEach((g) => {
        g.bullets.forEach((b) => recommendations.push(`${g.source} ${g.year ?? ""}: ${b}`));
      });
    } else if (moderate) {
      recommendations.push(...guidelines.flatMap((g) => g.bullets.slice(0, 2).map((b) => `${g.source}: ${b}`)));
    } else {
      recommendations.push(...guidelines.flatMap((g) => g.bullets.slice(0, 1).map((b) => `${g.source}: ${b}`)));
    }
  }

  // Generic lifestyle advice
  lifestyle_advice.push("Balanced diet with reduced processed sugars and saturated fats.");
  lifestyle_advice.push("Regular physical activity: aim for ≥150 min/week moderate exercise.");
  lifestyle_advice.push("Smoking cessation and limiting alcohol intake.");

  // Monitoring and follow-up by risk
  if (high) {
    follow_up_plan.push({ when: "Within 2 weeks", action: "Urgent clinician review and confirmatory testing as needed" });
    monitoring_schedule.push({ measure: "Blood pressure", frequency: "Weekly until controlled" });
    monitoring_schedule.push({ measure: "Relevant labs (e.g., HbA1c, eGFR)", frequency: "As soon as possible" });
    emergency_warning_signs.push("Severe chest pain, breathlessness, sudden weakness or speech difficulty, acute severe abdominal pain, severe bleeding");
  } else if (moderate) {
    follow_up_plan.push({ when: "4–12 weeks", action: "Arrange follow-up with primary care to repeat assessment and initiate preventive measures" });
    monitoring_schedule.push({ measure: "Routine vitals and relevant labs", frequency: "Every 1–3 months" });
    emergency_warning_signs.push("Worsening symptoms, new focal neurological deficits, worsening shortness of breath");
  } else {
    follow_up_plan.push({ when: "6 months", action: "Routine monitoring and reinforce prevention" });
    monitoring_schedule.push({ measure: "Routine check-up", frequency: "Annually or per risk" });
  }

  // Disease-specific augmentations
  if (disease) {
    const key = (disease || "").toLowerCase();
    if (key.includes("diabet") || key.includes("hba1c")) {
      monitoring_schedule.push({ measure: "HbA1c", frequency: high ? "Every 3 months" : "Every 3–6 months" });
      if (high) emergency_warning_signs.push("Symptoms of hyperglycemia or hypoglycemia requiring urgent care");
    }
    if (key.includes("heart") || key.includes("cardio") || key.includes("ascvd")) {
      monitoring_schedule.push({ measure: "Lipid profile", frequency: "Every 3–12 months based on therapy" });
      recommendations.push("Assess and treat cardiovascular risk factors (BP, lipids, smoking).");
    }
    if (key.includes("stroke")) {
      recommendations.push("Educate patient and caregivers on FAST stroke signs and seek immediate care.");
    }
    if (key.includes("kidney") || key.includes("renal")) {
      monitoring_schedule.push({ measure: "Urine albumin-to-creatinine ratio", frequency: "Annually or more frequently if abnormal" });
    }
    if (key.includes("liver") || key.includes("hepatitis")) {
      recommendations.push("Assess for viral hepatitis testing and evaluate for metabolic liver disease.");
    }
    if (key.includes("cancer") || key.includes("breast")) {
      recommendations.push("Follow local cancer pathway for urgent diagnostics and referral.");
    }
  }

  return {
    interpretation,
    guideline_references: guidelines,
    recommendations: Array.from(new Set(recommendations)),
    lifestyle_advice: Array.from(new Set(lifestyle_advice)),
    follow_up_plan,
    monitoring_schedule,
    emergency_warning_signs: Array.from(new Set(emergency_warning_signs)),
  };
}

export default { generateRecommendations };
