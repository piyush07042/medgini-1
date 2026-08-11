"""Clinical guideline library used to create Clinical Intelligence sections in reports.

Each entry contains: source, year, url, concise evidence-based recommendations,
screening/follow-up schedules, referral triggers, and emergency signs.
"""
from typing import Any, Dict, Optional


GUIDELINES: Dict[str, Dict[str, Any]] = {
    "diabetes": {
        "disease": "Diabetes Mellitus (Type 2)",
        "source": "ADA",
        "year": 2025,
        "url": "https://diabetes.org/clinical/practice-recommendations",
        "recommendations": [
            "Diagnose diabetes with HbA1c >= 6.5% or fasting plasma glucose >= 126 mg/dL or 2‑hour OGTT >= 200 mg/dL.",
            "Aim for individualized HbA1c target; typical target for many nonpregnant adults is ~7.0%, tighter targets (e.g., <6.5%) for select patients with low hypoglycemia risk.",
            "Lifestyle modification (diet, physical activity, weight management) is first‑line and should be implemented alongside pharmacotherapy when indicated.",
        ],
        "screening": [
            "Annual foot exam and annual diabetic retinopathy screening; more frequent monitoring if abnormalities found.",
            "Assess kidney function (eGFR) and urine albumin-to-creatinine ratio (ACR) at diagnosis and annually.",
        ],
        "follow_up": [
            "Monitor HbA1c every 3 months until stable, then at least every 6 months.",
            "Assess cardiovascular risk and optimize blood pressure and lipid management per guidelines.",
        ],
        "referral_triggers": [
            "Rapid decline in renal function (rising creatinine or eGFR fall) or ACR in nephrotic range: refer to nephrology.",
            "Vision changes suggestive of retinopathy: urgent ophthalmology referral.",
        ],
        "emergency_signs": [
            "Symptoms of hyperosmolar hyperglycemic state (marked polyuria, dehydration, confusion) or diabetic ketoacidosis (nausea, vomiting, abdominal pain): seek emergency care.",
        ],
    },

    "heart_disease": {
        "disease": "Atherosclerotic Cardiovascular Disease (ASCVD)",
        "source": "AHA/ACC",
        "year": 2023,
        "url": "https://www.heart.org/en/health-topics/clinical-practice-guidelines",
        "recommendations": [
            "Assess ASCVD risk using pooled cohort equations and apply individualized primary prevention strategies.",
            "For patients with established ASCVD, use high-intensity statin therapy unless contraindicated.",
            "Control blood pressure to guideline targets (generally <130/80 mmHg for most patients with high cardiovascular risk).",
        ],
        "screening": [
            "Periodic lipid profile and blood pressure measurement; monitor adherence and side effects of lipid-lowering therapy.",
        ],
        "follow_up": [
            "Routine cardiovascular risk factor review every 3–12 months depending on stability.",
            "Consider cardiac rehabilitation referral after acute coronary syndromes or revascularization.",
        ],
        "referral_triggers": [
            "New or worsening angina, syncope, or heart failure symptoms: urgent cardiology evaluation.",
        ],
        "emergency_signs": [
            "Chest pain suggestive of myocardial ischemia, sudden shortness of breath, or syncope: call emergency services immediately.",
        ],
    },

    "stroke": {
        "disease": "Ischemic Stroke / Stroke Risk",
        "source": "AHA/ASA",
        "year": 2023,
        "url": "https://www.stroke.org/en/professionals/clinical-resources",
        "recommendations": [
            "For atrial fibrillation-related stroke risk, use CHA2DS2-VASc to guide anticoagulation decisions.",
            "Implement blood pressure control and statin therapy to reduce recurrent stroke risk.",
        ],
        "screening": [
            "Assess for AF with pulse check and ECG in patients with stroke symptoms or high suspicion.",
        ],
        "follow_up": [
            "Early post-discharge follow-up within 1–2 weeks and multidisciplinary secondary prevention planning.",
        ],
        "referral_triggers": [
            "Acute focal neurological deficits, facial droop, weakness, or speech disturbance: immediate ED evaluation for possible thrombolysis/thrombectomy.",
        ],
        "emergency_signs": [
            "Sudden unilateral weakness, speech disturbance, vision loss, or severe headache: activate emergency stroke pathway.",
        ],
    },

    "kidney_disease": {
        "disease": "Chronic Kidney Disease (CKD)",
        "source": "KDIGO",
        "year": 2022,
        "url": "https://kdigo.org/guidelines/",
        "recommendations": [
            "Stage CKD by eGFR and albuminuria; implement ACEi/ARB for albuminuric CKD unless contraindicated.",
            "Optimize blood pressure and glycemic control to slow progression.",
        ],
        "screening": [
            "Measure eGFR and urine ACR at least annually for at-risk patients; more frequently if CKD stage progresses.",
        ],
        "follow_up": [
            "Refer to nephrology for rapidly progressive CKD, sustained eGFR <30 mL/min/1.73m2, or refractory albuminuria.",
        ],
        "referral_triggers": [
            "Rapid decline in eGFR, refractory hyperkalemia, or uncontrolled fluid overload: urgent nephrology referral.",
        ],
        "emergency_signs": [
            "Symptoms of uremia (nausea, vomiting, confusion), severe hyperkalemia, or pulmonary edema: emergency care required.",
        ],
    },

    "liver_disease": {
        "disease": "Chronic Liver Disease / Cirrhosis",
        "source": "AASLD",
        "year": 2023,
        "url": "https://www.aasld.org/publications/practice-guidelines-0",
        "recommendations": [
            "Evaluate chronic liver disease with appropriate serologies, imaging, and noninvasive fibrosis assessment; manage portal hypertension and complications per guidelines.",
            "For suspected NAFLD/NASH, implement weight loss, optimize metabolic risk factors, and consider specialist referral for advanced disease.",
        ],
        "screening": [
            "Surveillance for hepatocellular carcinoma in cirrhotic patients with ultrasound +/- AFP every 6 months.",
        ],
        "follow_up": [
            "Monitor liver synthetic function (INR, albumin), bilirubin, and portal hypertension signs; schedule specialist follow-up for progressive disease.",
        ],
        "referral_triggers": [
            "New-onset jaundice, ascites, encephalopathy, or GI bleeding: urgent hepatology assessment.",
        ],
        "emergency_signs": [
            "Altered mental status, massive GI bleed, or progressive jaundice: seek immediate emergency care.",
        ],
    },

    "breast_cancer": {
        "disease": "Breast Cancer (screening & referral)",
        "source": "NCCN",
        "year": 2024,
        "url": "https://www.nccn.org/guidelines/category_1",
        "recommendations": [
            "Adhere to age- and risk-based screening (mammography starting age per risk profile); refer suspicious imaging/lesions for diagnostic workup and biopsy.",
            "For newly suspected malignancy, expedite breast surgery/oncology referral and staging workup.",
        ],
        "screening": [
            "Annual or biennial screening mammography as per risk and local guideline recommendations; MRI for high-risk patients.",
        ],
        "follow_up": [
            "Timely oncology multidisciplinary evaluation for confirmed diagnoses; discuss systemic therapy, surgery, and radiation as appropriate.",
        ],
        "referral_triggers": [
            "Palpable mass, suspicious imaging (BI-RADS 4/5), or skin/nipple changes: urgent breast clinic referral.",
        ],
        "emergency_signs": [
            "Rapidly enlarging mass with pain, ulceration, or active bleeding requires urgent evaluation.",
        ],
    },

    "parkinsons": {
        "disease": "Parkinson's Disease",
        "source": "AAN",
        "year": 2021,
        "url": "https://www.aan.com/Guidelines/",
        "recommendations": [
            "Diagnose Parkinsonism clinically; consider referral to neurology for atypical features or rapid progression.",
            "Initiate symptomatic therapy individualized to motor symptoms and patient goals; consider multidisciplinary care for motor and nonmotor symptoms.",
        ],
        "screening": [
            "Assess for falls, swallowing dysfunction, cognitive impairment, and orthostatic hypotension at baseline and periodically.",
        ],
        "follow_up": [
            "Neurology follow-up at regular intervals and earlier if new red flags or progression of disability.",
        ],
        "referral_triggers": [
            "Rapid decline, early autonomic failure, poor levodopa response, or atypical features: refer to movement disorders specialist.",
        ],
        "emergency_signs": [
            "Acute severe motor fluctuations with inability to ambulate, aspiration, or acute psychosis: urgent evaluation.",
        ],
    },

    "hepatitis": {
        "disease": "Viral Hepatitis / Chronic Hepatitis",
        "source": "WHO / AASLD",
        "year": 2023,
        "url": "https://www.who.int/health-topics/hepatitis;https://www.aasld.org/",
        "recommendations": [
            "Screen at-risk populations for hepatitis B and C; offer antiviral therapy per genotype and stage, aiming for viral suppression or cure.",
            "Vaccinate susceptible individuals for hepatitis B where indicated.",
        ],
        "screening": [
            "Check hepatitis B surface antigen, hepatitis C antibody, and confirmatory testing in at-risk individuals or abnormal LFTs.",
        ],
        "follow_up": [
            "Monitor viral loads, liver enzymes, and fibrosis markers; arrange hepatology follow-up for chronic infection or advanced fibrosis.",
        ],
        "referral_triggers": [
            "Evidence of cirrhosis, hepatocellular carcinoma risk, or decompensation: urgent hepatology referral.",
        ],
        "emergency_signs": [
            "Severe jaundice, encephalopathy, coagulopathy, or GI bleeding: emergency care needed.",
        ],
    },

    "thyroid": {
        "disease": "Thyroid Disorders",
        "source": "ATA",
        "year": 2023,
        "url": "https://www.thyroid.org/clinical-practice-guidelines/",
        "recommendations": [
            "Evaluate abnormal TSH with reflex free T4; treat hypothyroidism with levothyroxine titrated to target TSH, treat hyperthyroidism according to etiology.",
            "Consider ultrasound and endocrinology referral for nodules or suspicious features.",
        ],
        "screening": [
            "Targeted screening in high-risk individuals (e.g., prior head/neck radiation, family history, pregnancy).",
        ],
        "follow_up": [
            "Repeat thyroid function testing 6–8 weeks after therapy change and annually when stable.",
        ],
        "referral_triggers": [
            "Severely abnormal TSH with symptoms, large goiter, or suspicious thyroid nodule: refer to endocrinology or ENT.",
        ],
        "emergency_signs": [
            "Thyroid storm (fever, delirium, tachycardia) or myxedema coma (hypothermia, obtundation): immediate emergency treatment.",
        ],
    },
}


def _normalize_key(key: Optional[str]) -> Optional[str]:
    if not key:
        return None
    k = key.lower().strip()
    k = k.replace(" ", "_")
    return k


def get_clinical_guideline(disease_key: Optional[str]) -> Dict[str, Any]:
    """Return the guideline entry best matching the disease key.

    Accepts common names or keys and performs a simple lookup.
    """
    if not disease_key:
        return {}
    k = _normalize_key(disease_key)

    # direct match
    if k in GUIDELINES:
        return GUIDELINES[k]

    # try contains match
    for gk, entry in GUIDELINES.items():
        if gk in k or (entry.get("disease") and entry.get("disease").lower() in k):
            return entry

    return {}
