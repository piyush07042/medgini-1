export type GuidelineEntry = {
  source: string;
  year?: string | number;
  url?: string;
  bullets: string[];
};

export type ClinicalGuidelines = Record<string, GuidelineEntry[]>;

// Concise, non-copy-protected summaries mapped by disease keyword.
const GUIDELINES: ClinicalGuidelines = {
  diabetes: [
    {
      source: "ADA",
      year: "2025",
      url: "",
      bullets: ["HbA1c >6.5% indicates diabetes.", "Recommend lifestyle intervention (diet, exercise).", "Annual retinal exam.", "Kidney (eGFR/albuminuria) screening annually."],
    },
    {
      source: "WHO",
      year: "2023",
      url: "",
      bullets: ["Promote community-level prevention through diet and physical activity.", "Prioritize affordable essential medicines and diagnostics."],
    },
  ],

  "heart disease": [
    {
      source: "AHA/ACC",
      year: "2024",
      url: "",
      bullets: ["Assess ASCVD risk and manage lipids per guideline.", "Recommend BP control and lifestyle modification.", "Consider statin therapy when indicated."],
    },
    {
      source: "ESC",
      year: "2023",
      url: "",
      bullets: ["Use risk scoring for primary prevention and tailor therapy.", "Emphasize smoking cessation and exercise."],
    },
  ],

  stroke: [
    {
      source: "AHA/ASA",
      year: "2024",
      url: "",
      bullets: ["Control blood pressure aggressively to reduce stroke risk.", "Antiplatelet therapy when appropriate.", "Rapid referral for acute stroke symptoms."],
    },
  ],

  kidney: [
    {
      source: "KDIGO",
      year: "2023",
      url: "",
      bullets: ["Screen high-risk patients for albuminuria and reduced eGFR.", "Optimize BP and glycemic control to slow progression.", "Refer to nephrology for advanced CKD or rapid decline."],
    },
  ],

  cancer: [
    {
      source: "NCCN",
      year: "2024",
      url: "",
      bullets: ["Follow cancer-specific screening and referral pathways.", "Urgent diagnostic workup for suspicious findings."],
    },
  ],

  liver: [
    {
      source: "AASLD",
      year: "2023",
      url: "",
      bullets: ["Screen for viral hepatitis where indicated.", "Assess for advanced fibrosis and manage metabolic risk factors."],
    },
  ],

  neurology: [
    {
      source: "AAN",
      year: "2023",
      url: "",
      bullets: ["Use disorder-specific diagnostic criteria and early specialist referral.", "Consider supportive therapies and safety planning."],
    },
  ],
};

export function findGuidelinesForDisease(disease?: string | null): GuidelineEntry[] {
  if (!disease) return [];
  const key = disease.toLowerCase();

  // Direct keys
  if ((GUIDELINES as any)[key]) return (GUIDELINES as any)[key];

  // Heuristics
  if (key.includes("diabet") || key.includes("hba1c")) return GUIDELINES.diabetes;
  if (key.includes("heart") || key.includes("cardio") || key.includes("ascvd")) return GUIDELINES["heart disease"];
  if (key.includes("stroke")) return GUIDELINES.stroke;
  if (key.includes("kidney") || key.includes("ckd") || key.includes("renal")) return GUIDELINES.kidney;
  if (key.includes("cancer") || key.includes("breast") || key.includes("oncology")) return GUIDELINES.cancer;
  if (key.includes("liver") || key.includes("hepatic") || key.includes("hepatitis")) return GUIDELINES.liver;
  if (key.includes("park") || key.includes("parkinson")) return GUIDELINES.neurology;

  return [];
}

export default GUIDELINES;
