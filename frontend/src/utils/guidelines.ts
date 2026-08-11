export type Guideline = {
  source: string;
  year?: string | number;
  bullets: string[];
};

const GUIDELINES: Record<string, Guideline> = {
  ADA: {
    source: "ADA Standards of Care in Diabetes",
    year: "2025",
    bullets: [
      "HbA1c >= 6.5% or Fasting Glucose >= 126 mg/dL for diagnosis.",
      "Lifestyle modifications (diet, weight loss 5-7%, 150+ min/week exercise).",
      "Metformin as first-line pharmacotherapy if not contraindicated.",
      "Annual dilated retinal exam, kidney screening (uACR), and comprehensive foot exam."
    ]
  },
  AHA: {
    source: "AHA/ACC Cardiovascular Prevention Guidelines",
    year: "2025",
    bullets: [
      "Target Blood Pressure < 130/80 mmHg.",
      "Moderate-to-high intensity statin for high cardiovascular risk (target LDL-C reduction >= 50%).",
      "Lifestyle adjustments: DASH/Mediterranean diet, 150+ min/week aerobic exercise.",
      "Discuss low-dose aspirin (75-100 mg/day) if high risk and low bleeding hazard."
    ]
  },
  KDIGO: {
    source: "KDIGO Clinical Practice Guideline for CKD",
    year: "2024",
    bullets: [
      "SGLT2 inhibitor as first-line therapy if eGFR >= 20 mL/min/1.73m².",
      "Maximum tolerated dose of ACEi or ARB for patients with hypertension and albuminuria.",
      "Dietary sodium restriction (< 2 g/day).",
      "Avoid nephrotoxins such as NSAIDs, aminoglycosides, and contrast media."
    ]
  },
  ASA: {
    source: "AHA/ASA Guidelines for the Prevention of Stroke",
    year: "2024",
    bullets: [
      "Antiplatelet therapy (aspirin 81 mg/day or clopidogrel 75 mg/day) for secondary prevention.",
      "High-intensity statin to target LDL-C < 70 mg/dL.",
      "Tight blood pressure control aiming for < 130/80 mmHg.",
      "Screen for atrial fibrillation if stroke is of undetermined source."
    ]
  },
  ESC: {
    source: "ESC/ACC Heart Failure Guidelines",
    year: "2023",
    bullets: [
      "Initiate quadruple therapy: ARNI/ACEi, Beta-blocker, MRA, and SGLT2 inhibitor for HFrEF.",
      "Titrate to target doses used in major trials as tolerated.",
      "Sodium restriction < 2-3 g/day and daily monitoring of patient weight.",
      "Avoid nondihydropyridine calcium channel blockers and NSAIDs."
    ]
  },
  AASLD: {
    source: "AASLD/EASL Practice Guidance on NAFLD/NASH",
    year: "2023",
    bullets: [
      "Recommend structured lifestyle interventions targeting >= 7-10% weight loss.",
      "Complete avoidance of alcohol consumption.",
      "Screen for and optimize metabolic risk factors (diabetes, HTN, dyslipidemia).",
      "Consider non-invasive staging (elastography) or liver biopsy for diagnosis."
    ]
  },
  WHO: {
    source: "WHO/AASLD Guidelines for Chronic Hepatitis B",
    year: "2024",
    bullets: [
      "Initiate antiviral therapy (tenofovir or entecavir) for high HBV DNA and elevated ALT.",
      "Ensure strict patient adherence to treatment and screen close contacts.",
      "Regular monitor of renal functions (especially if on Tenofovir TDF).",
      "Semiannual HCC screening with ultrasound in high-risk patients."
    ]
  },
  NCCN: {
    source: "NCCN Clinical Practice Guidelines: Breast Cancer",
    year: "2024",
    bullets: [
      "Refer to genetic counselor if hereditary risk factors are present.",
      "Annual screening mammogram beginning at age 40 (or earlier if high-risk).",
      "Discuss risk reduction chemoprevention (e.g., tamoxifen, raloxifene).",
      "Counsel on lifestyle: weight management, physical activity, alcohol restriction."
    ]
  },
  AAN: {
    source: "AAN Guidelines on Parkinson's Disease Management",
    year: "2023",
    bullets: [
      "Neurologist referral for definitive diagnosis and customized management plan.",
      "Consider levodopa or dopamine agonists to manage motor deficits.",
      "Physical and occupational therapy referral for safety and gait training.",
      "Screen regularly for non-motor symptoms (sleep, depression, cognition)."
    ]
  },
  NICE: {
    source: "NICE Clinical Guidelines (UK)",
    year: "2024",
    bullets: [
      "Offer lifestyle advice to all people with suspected hypertension or high risk.",
      "Target clinic blood pressure of < 140/90 mmHg for people aged under 80.",
      "Use HbA1c for monitoring blood glucose levels every 3-6 months.",
      "Prioritize patient education and structured self-management programs."
    ]
  },
  CDC: {
    source: "CDC Prevention & Screening Recommendations",
    year: "2024",
    bullets: [
      "Screen all adults aged 18 to 79 at least once in their lifetime for Hepatitis B/C.",
      "Recommend standard immunization schedules and vaccine updates.",
      "Implement comprehensive physical activity guidelines: 150+ minutes of aerobic exercise/week.",
      "Maintain active surveillance for chronic metabolic and infectious diseases."
    ]
  },
  USPSTF: {
    source: "USPSTF Preventive Services Recommendations",
    year: "2024",
    bullets: [
      "Screening mammography biennially for women aged 40 to 74.",
      "Screen for prediabetes and type 2 diabetes in asymptomatic adults aged 35 to 70 who are overweight or obese.",
      "Initiate low-to-moderate dose statins for primary prevention of CVD if risk score is high.",
      "Offer behavioral counseling interventions for lifestyle improvements."
    ]
  }
};

export function getGuidelineFor(disease: string | undefined | null) {
  if (!disease) return null;
  const key = disease.toLowerCase().replace(/_/g, " ");

  if (key.includes("diabetes") || key.includes("diabetic") || key.includes("hba1c")) {
    return GUIDELINES.ADA;
  }
  if (key.includes("heart failure") || key.includes("hfref")) {
    return GUIDELINES.ESC;
  }
  if (key.includes("heart") || key.includes("cardio") || key.includes("coronary")) {
    return GUIDELINES.AHA;
  }
  if (key.includes("kidney") || key.includes("renal") || key.includes("nephro") || key.includes("ckd")) {
    return GUIDELINES.KDIGO;
  }
  if (key.includes("stroke") || key.includes("tia") || key.includes("cerebro")) {
    return GUIDELINES.ASA;
  }
  if (key.includes("liver") || key.includes("hepatic") || key.includes("nash") || key.includes("nafld")) {
    return GUIDELINES.AASLD;
  }
  if (key.includes("hepatitis")) {
    return GUIDELINES.WHO;
  }
  if (key.includes("breast") || key.includes("cancer") || key.includes("mammogram")) {
    return GUIDELINES.NCCN;
  }
  if (key.includes("parkinson")) {
    return GUIDELINES.AAN;
  }

  return null;
}

export default GUIDELINES;
