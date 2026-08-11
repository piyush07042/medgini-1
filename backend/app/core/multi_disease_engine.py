import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Organ System Weights for Health Index calculation
SYSTEM_WEIGHTS = {
    "cardiovascular": 0.25,
    "metabolic": 0.20,
    "renal": 0.15,
    "hepatic": 0.15,
    "neurological": 0.15,
    "oncological": 0.10
}

def calculate_combined_disease_risk(predictions_map: Dict[str, Any], patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates combined disease risk across organ systems.
    returns organ_scores, combined_risk_percent, and risk_category.
    """
    # Normalize probabilities for each disease
    scores = {
        "cardiovascular": 0.0,
        "metabolic": 0.0,
        "renal": 0.0,
        "hepatic": 0.0,
        "neurological": 0.0,
        "oncological": 0.0
    }

    # Helper to get score float
    def get_prob(key_names: List[str]) -> float:
        for k in key_names:
            if k in predictions_map:
                val = predictions_map[k]
                if isinstance(val, dict):
                    return float(val.get("probability") or val.get("confidence") or val.get("risk_score") or 0.0)
                elif isinstance(val, (int, float)):
                    return float(val)
        return 0.0

    scores["cardiovascular"] = max(get_prob(["heart_disease", "heart_failure", "stroke"]), 0.0)
    scores["metabolic"] = max(get_prob(["diabetes"]), 0.0)
    scores["renal"] = max(get_prob(["kidney_disease"]), 0.0)
    scores["hepatic"] = max(get_prob(["liver_disease", "hepatitis"]), 0.0)
    scores["neurological"] = max(get_prob(["parkinsons"]), 0.0)
    scores["oncological"] = max(get_prob(["breast_cancer"]), 0.0)

    # Calculate weighted combined risk
    weighted_sum = sum(scores[system] * SYSTEM_WEIGHTS[system] for system in SYSTEM_WEIGHTS)
    # Check max individual risk to avoid diluting acute single-organ high risk
    max_risk = max(scores.values()) if scores.values() else 0.0
    
    # Combined risk is the higher of max_risk or weighted compounding
    combined_risk_prob = round(max(max_risk * 0.85, weighted_sum * 1.2), 3)
    combined_risk_prob = min(1.0, combined_risk_prob)
    combined_risk_percent = round(combined_risk_prob * 100, 1)

    if combined_risk_percent >= 75:
        risk_category = "Critical"
    elif combined_risk_percent >= 50:
        risk_category = "High"
    elif combined_risk_percent >= 25:
        risk_category = "Moderate"
    else:
        risk_category = "Low"

    return {
        "organ_scores": {k: round(v * 100, 1) for k, v in scores.items()},
        "combined_risk_percent": combined_risk_percent,
        "combined_risk_probability": combined_risk_prob,
        "risk_category": risk_category
    }

def calculate_overall_health_score(combined_risk_percent: float, patient_age: int, lab_abnormalities_count: int = 0) -> Dict[str, Any]:
    """
    Computes MediGenie 0-100 Health Index Score (100 = Optimal Health).
    """
    base = 100.0 - combined_risk_percent
    
    # Age factor penalty (slight penalty for age > 65 with comorbidities)
    age_penalty = 0.0
    if patient_age > 65:
        age_penalty = min(10.0, (patient_age - 65) * 0.4)
        
    lab_penalty = min(15.0, lab_abnormalities_count * 3.0)

    final_score = round(max(5.0, base - age_penalty - lab_penalty), 1)

    if final_score >= 80:
        status = "Optimal"
    elif final_score >= 60:
        status = "Fair"
    elif final_score >= 40:
        status = "Guarded"
    else:
        status = "Critical"

    return {
        "health_score": final_score,
        "status": status,
        "description": f"Overall Health Index is rated {status} ({final_score}/100)."
    }

def detect_comorbidities(patient_data: Dict[str, Any], predictions_map: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detects clinical comorbidity clusters and syndromes.
    """
    clusters = []

    # Extract metrics & risks
    glucose = float(patient_data.get("glucose") or patient_data.get("fasting_blood_sugar") or 0)
    systolic_bp = float(patient_data.get("systolic_bp") or patient_data.get("blood_pressure") or 0)
    bmi = float(patient_data.get("bmi") or 0)
    egfr = float(patient_data.get("egfr") or 90)

    diabetes_risk = float((predictions_map.get("diabetes") or {}).get("probability") or 0)
    heart_risk = float((predictions_map.get("heart_disease") or predictions_map.get("heart_failure") or {}).get("probability") or 0)
    kidney_risk = float((predictions_map.get("kidney_disease") or {}).get("probability") or 0)
    liver_risk = float((predictions_map.get("liver_disease") or predictions_map.get("hepatitis") or {}).get("probability") or 0)

    # Cluster 1: Metabolic Syndrome
    if (glucose >= 100 or diabetes_risk >= 0.5) and (systolic_bp >= 130) and (bmi >= 25):
        clusters.append({
            "name": "Metabolic Syndrome",
            "severity": "High" if (glucose >= 126 and systolic_bp >= 140) else "Moderate",
            "criteria_met": ["Elevated Fasting Glucose / Diabetes Risk", "Hypertension", "Overweight / Obesity"],
            "recommendation": "Intensive multi-factorial intervention focusing on weight reduction, glycemic control, and blood pressure optimization."
        })

    # Cluster 2: Cardiorenal-Metabolic (CKM) Syndrome
    if (heart_risk >= 0.4 or systolic_bp >= 140) and (kidney_risk >= 0.4 or egfr < 60) and (diabetes_risk >= 0.4 or glucose >= 126):
        clusters.append({
            "name": "Cardiorenal-Metabolic (CKM) Syndrome",
            "severity": "Critical",
            "criteria_met": ["Cardiovascular Disease Risk", "Renal Impairment / CKD Risk", "Glycemic Dysregulation"],
            "recommendation": "Priority co-management by Cardiology, Nephrology, and Endocrinology. Initiate SGLT2 inhibitor + ARNI/ACEi if tolerated."
        })

    # Cluster 3: Hepatorenal Syndrome Risk
    if (liver_risk >= 0.5) and (kidney_risk >= 0.5 or egfr < 60):
        clusters.append({
            "name": "Hepatorenal Risk Synergy",
            "severity": "High",
            "criteria_met": ["Hepatic Dysfunction", "Renal Clearance Decline"],
            "recommendation": "Careful fluid balance management, avoid nephrotoxic drugs, monitor serum creatinine and ALT/AST closely."
        })

    # Cluster 4: Vascular Synergy (Stroke + Heart)
    stroke_risk = float((predictions_map.get("stroke") or {}).get("probability") or 0)
    if heart_risk >= 0.5 and stroke_risk >= 0.5:
        clusters.append({
            "name": "Systemic Atherosclerotic Risk",
            "severity": "Critical",
            "criteria_met": ["Coronary Artery Disease Risk", "Cerebrovascular Stroke Risk"],
            "recommendation": "High-intensity statin therapy, antithrombotic management, and strict blood pressure control < 130/80 mmHg."
        })

    return clusters

def analyze_disease_interactions(predictions_map: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analyzes cross-disease compounding risks and interactions.
    """
    interactions = []

    d_prob = float((predictions_map.get("diabetes") or {}).get("probability") or 0)
    k_prob = float((predictions_map.get("kidney_disease") or {}).get("probability") or 0)
    h_prob = float((predictions_map.get("heart_disease") or predictions_map.get("heart_failure") or {}).get("probability") or 0)
    s_prob = float((predictions_map.get("stroke") or {}).get("probability") or 0)
    l_prob = float((predictions_map.get("liver_disease") or {}).get("probability") or 0)

    if d_prob >= 0.5 and k_prob >= 0.5:
        interactions.append({
            "primary_disease": "Diabetes",
            "interacting_disease": "Kidney Disease",
            "effect": "Diabetic Nephropathy Acceleration",
            "description": "Uncontrolled glycemic risk exponentially increases glomerulosclerosis, reducing eGFR 2x faster.",
            "action": "Add SGLT2 inhibitor to slow CKD progression."
        })

    if d_prob >= 0.5 and h_prob >= 0.5:
        interactions.append({
            "primary_disease": "Diabetes",
            "interacting_disease": "Heart Disease",
            "effect": "Cardiovascular Complication Compounding",
            "description": "Diabetes increases vascular inflammation and risk of myocardial infarction by 2-4x.",
            "action": "Target LDL-C < 70 mg/dL and consider GLP-1 receptor agonist with proven CVD benefit."
        })

    if h_prob >= 0.5 and s_prob >= 0.5:
        interactions.append({
            "primary_disease": "Heart Disease",
            "interacting_disease": "Stroke",
            "effect": "Cerebrovascular Event Synergy",
            "description": "Co-existing coronary disease and stroke risk indicates widespread arterial plaque.",
            "action": "Ensure high-intensity statin and antiplatelet regimen."
        })

    if l_prob >= 0.5 and d_prob >= 0.5:
        interactions.append({
            "primary_disease": "Liver Disease",
            "interacting_disease": "Diabetes",
            "effect": "NASH & Insulin Resistance Loop",
            "description": "Hepatic steatosis worsens insulin resistance, creating a progressive metabolic cycle.",
            "action": "Target 7-10% body weight reduction; evaluate pioglitazone or GLP-1 RA."
        })

    return interactions

def generate_longitudinal_risk_timeline(prediction_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Builds a risk trajectory timeline over sequential patient visits/predictions.
    """
    timeline = []
    for item in prediction_history:
        disease = item.get("disease", "Clinical Assessment")
        prob = item.get("probability", 0.0)
        date = item.get("createdAt") or item.get("date") or datetime.now().strftime("%Y-%m-%d")
        category = item.get("confidenceLabel") or item.get("risk_category") or ("High" if prob >= 0.6 else "Low")
        
        timeline.append({
            "date": date,
            "disease": disease,
            "risk_score_percent": round(prob * 100, 1),
            "risk_category": category,
            "summary": item.get("summary", f"{disease} risk evaluated at {round(prob * 100, 1)}%")
        })

    # Sort chronologically
    timeline.sort(key=lambda x: x["date"])
    return timeline

def build_unified_patient_summary(
    patient_data: Dict[str, Any],
    predictions_map: Dict[str, Any],
    prediction_history: List[Dict[str, Any]] | None = None
) -> Dict[str, Any]:
    """
    Facade function generating complete Multi-Disease Intelligence payload.
    """
    combined_risk = calculate_combined_disease_risk(predictions_map, patient_data)
    patient_age = int(patient_data.get("age", 45) or 45)
    
    # Count lab abnormalities
    abnormalities = 0
    if float(patient_data.get("glucose", 0) or 0) >= 126: abnormalities += 1
    if float(patient_data.get("systolic_bp", 0) or 0) >= 140: abnormalities += 1
    if float(patient_data.get("bmi", 0) or 0) >= 30: abnormalities += 1
    if float(patient_data.get("egfr", 90) or 90) < 60: abnormalities += 1

    health_index = calculate_overall_health_score(combined_risk["combined_risk_percent"], patient_age, abnormalities)
    comorbidities = detect_comorbidities(patient_data, predictions_map)
    interactions = analyze_disease_interactions(predictions_map)
    timeline = generate_longitudinal_risk_timeline(prediction_history or [])

    return {
        "combined_risk": combined_risk,
        "health_index": health_index,
        "comorbidities": comorbidities,
        "disease_interactions": interactions,
        "longitudinal_timeline": timeline,
        "abnormalities_count": abnormalities,
        "evaluated_at": datetime.now().isoformat()
    }
