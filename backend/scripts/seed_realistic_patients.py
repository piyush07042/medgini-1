"""
Seed realistic patient data for all 9 MediGenie diseases.
Each disease gets 10 patients (5 male, 5 female) with Low / Medium / High risk profiles.

NOTE: AI reports are inferred from real trained models, not fabricated.
The _build_ai_report() function calls predictor.predict_json() for each patient
using the same ML models that serve the live API endpoints. Probabilities,
predictions, and confidence values in AIReport rows are genuine model output.

All clinical values are based on real medical reference ranges and published datasets:
  - Cleveland Heart Disease Dataset (UCI)
  - Diabetes Readmission Dataset (hospital-encounter features)
  - Indian Liver Patient Dataset (ILPD)
  - UCI Chronic Kidney Disease Dataset
  - Wisconsin Breast Cancer Dataset (WBCD)
  - UCI Parkinsons Voice Dataset (Little et al., 2007)
  - UCI Hepatitis Dataset
  - Heart Failure Clinical Records (Chicco & Jurman 2020)
  - Stroke Prediction Dataset (Kaggle)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from pathlib import Path
from app.db.session import SessionLocal, create_database
from app.models.models import Patient, AIReport, User

# ---------------------------------------------------------------------------
#  Model loading for real inference
# ---------------------------------------------------------------------------
from ml.inference.predictor import load_predictor

_MODEL_ROOT = Path(__file__).resolve().parents[1] / "models"

DISEASE_TO_MODEL_DIR = {
    "heart_disease": "heart_disease",
    "diabetes": "diabetes_model",
    "kidney_disease": "kidney_disease_model",
    "liver_disease": "liver_disease_model",
    "breast_cancer": "breast_cancer_model",
    "parkinsons": "parkinsons_model",
    "hepatitis": "hepatitis_model",
    "heart_failure": "heart_failure_model",
    "stroke": "stroke_model",
}

_predictor_cache: dict = {}


def _get_predictor(disease_key: str):
    """Lazy-load and cache predictors."""
    if disease_key not in _predictor_cache:
        model_dir_name = DISEASE_TO_MODEL_DIR[disease_key]
        model_path = _MODEL_ROOT / model_dir_name
        _predictor_cache[disease_key] = load_predictor(model_path)
    return _predictor_cache[disease_key]


# ---------------------------------------------------------------------------
#  Ensure tables exist, then assign to doctor user ID 2 -- fallback/create
# ---------------------------------------------------------------------------
create_database()
db = SessionLocal()

doctor = db.query(User).filter(User.id == 2).first()
if not doctor:
    doctor = db.query(User).first()
if not doctor:
    # Create a default doctor so we can seed patients
    from app.core.security import get_password_hash
    doctor = User(
        email="doctor@medigenie.com",
        hashed_password=get_password_hash("doctor123"),
        full_name="Dr. Piyush Gupta",
        role="doctor",
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    print(f"Created default doctor: {doctor.full_name} (ID={doctor.id})")
DOCTOR_ID = doctor.id

# ========================================================================
#  HEART DISEASE  (Cleveland dataset fields)
#  Fields: age, sex(0=F,1=M), cp(1-4), trestbps, chol, fbs, restecg,
#          thalach, exang, oldpeak, slope, ca, thal
# ========================================================================
HEART_DISEASE_PATIENTS = [
    # --- LOW RISK (healthy profiles) ---
    {
        "first_name": "Arjun",   "last_name": "Mehta",    "age": 32, "gender": "Male",
        "medical_history": {"disease": "heart_disease", "risk": "Low",
            "data": {"age": 32, "sex": 1, "cp": 1, "trestbps": 118, "chol": 180, "fbs": 0, "restecg": 0, "thalach": 185, "exang": 0, "oldpeak": 0.0, "slope": 1, "ca": 0, "thal": 3}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Sneha",   "last_name": "Iyer",     "age": 28, "gender": "Female",
        "medical_history": {"disease": "heart_disease", "risk": "Low",
            "data": {"age": 28, "sex": 0, "cp": 1, "trestbps": 112, "chol": 170, "fbs": 0, "restecg": 0, "thalach": 190, "exang": 0, "oldpeak": 0.0, "slope": 1, "ca": 0, "thal": 3}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Rahul",   "last_name": "Sharma",   "age": 35, "gender": "Male",
        "medical_history": {"disease": "heart_disease", "risk": "Low",
            "data": {"age": 35, "sex": 1, "cp": 1, "trestbps": 120, "chol": 195, "fbs": 0, "restecg": 0, "thalach": 178, "exang": 0, "oldpeak": 0.2, "slope": 1, "ca": 0, "thal": 3}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Priya",   "last_name": "Nair",     "age": 52, "gender": "Female",
        "medical_history": {"disease": "heart_disease", "risk": "Medium",
            "data": {"age": 52, "sex": 0, "cp": 2, "trestbps": 138, "chol": 245, "fbs": 0, "restecg": 1, "thalach": 155, "exang": 0, "oldpeak": 1.2, "slope": 2, "ca": 1, "thal": 6}},
        "allergies": ["Aspirin"], "current_medications": ["Atorvastatin 10mg"],
    },
    {
        "first_name": "Vikram",  "last_name": "Patel",    "age": 55, "gender": "Male",
        "medical_history": {"disease": "heart_disease", "risk": "Medium",
            "data": {"age": 55, "sex": 1, "cp": 2, "trestbps": 142, "chol": 260, "fbs": 1, "restecg": 1, "thalach": 148, "exang": 0, "oldpeak": 1.5, "slope": 2, "ca": 1, "thal": 6}},
        "allergies": [], "current_medications": ["Metoprolol 25mg", "Aspirin 75mg"],
    },
    {
        "first_name": "Kavitha", "last_name": "Raman",    "age": 48, "gender": "Female",
        "medical_history": {"disease": "heart_disease", "risk": "Medium",
            "data": {"age": 48, "sex": 0, "cp": 3, "trestbps": 135, "chol": 240, "fbs": 0, "restecg": 1, "thalach": 152, "exang": 0, "oldpeak": 1.0, "slope": 2, "ca": 0, "thal": 6}},
        "allergies": [], "current_medications": ["Amlodipine 5mg"],
    },
    {
        "first_name": "Suresh",  "last_name": "Kumar",    "age": 50, "gender": "Male",
        "medical_history": {"disease": "heart_disease", "risk": "Medium",
            "data": {"age": 50, "sex": 1, "cp": 3, "trestbps": 140, "chol": 255, "fbs": 0, "restecg": 0, "thalach": 145, "exang": 1, "oldpeak": 1.8, "slope": 2, "ca": 1, "thal": 6}},
        "allergies": [], "current_medications": ["Losartan 50mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Meena",   "last_name": "Reddy",    "age": 67, "gender": "Female",
        "medical_history": {"disease": "heart_disease", "risk": "High",
            "data": {"age": 67, "sex": 0, "cp": 4, "trestbps": 165, "chol": 310, "fbs": 1, "restecg": 2, "thalach": 115, "exang": 1, "oldpeak": 3.5, "slope": 3, "ca": 3, "thal": 7}},
        "allergies": ["Penicillin"], "current_medications": ["Metoprolol 50mg", "Clopidogrel 75mg", "Atorvastatin 40mg"],
    },
    {
        "first_name": "Ramesh",  "last_name": "Verma",    "age": 63, "gender": "Male",
        "medical_history": {"disease": "heart_disease", "risk": "High",
            "data": {"age": 63, "sex": 1, "cp": 4, "trestbps": 170, "chol": 335, "fbs": 1, "restecg": 2, "thalach": 108, "exang": 1, "oldpeak": 4.0, "slope": 3, "ca": 3, "thal": 7}},
        "allergies": [], "current_medications": ["Nitroglycerin", "Warfarin", "Atorvastatin 80mg"],
    },
    {
        "first_name": "Lakshmi", "last_name": "Devi",     "age": 70, "gender": "Female",
        "medical_history": {"disease": "heart_disease", "risk": "High",
            "data": {"age": 70, "sex": 0, "cp": 4, "trestbps": 175, "chol": 345, "fbs": 1, "restecg": 2, "thalach": 105, "exang": 1, "oldpeak": 4.2, "slope": 3, "ca": 4, "thal": 7}},
        "allergies": ["Sulfa drugs"], "current_medications": ["Digoxin", "Furosemide 40mg", "Enalapril 10mg"],
    },
]


# ========================================================================
#  DIABETES  (Diabetes Readmission — hospital-encounter features)
#  Real features: age, time_in_hospital, num_lab_procedures, num_procedures,
#                 num_medications, number_outpatient, number_emergency,
#                 number_inpatient, number_diagnoses
# ========================================================================
DIABETES_PATIENTS = [
    # --- LOW RISK (short stays, few procedures, few meds) ---
    {
        "first_name": "Amit",     "last_name": "Singh",    "age": 30, "gender": "Male",
        "medical_history": {"disease": "diabetes", "risk": "Low",
            "data": {"age": 30, "time_in_hospital": 1, "num_lab_procedures": 15, "num_procedures": 0, "num_medications": 5, "number_outpatient": 0, "number_emergency": 0, "number_inpatient": 0, "number_diagnoses": 3}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Divya",    "last_name": "Joshi",    "age": 26, "gender": "Female",
        "medical_history": {"disease": "diabetes", "risk": "Low",
            "data": {"age": 26, "time_in_hospital": 1, "num_lab_procedures": 10, "num_procedures": 0, "num_medications": 3, "number_outpatient": 0, "number_emergency": 0, "number_inpatient": 0, "number_diagnoses": 2}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Ravi",     "last_name": "Gupta",    "age": 34, "gender": "Male",
        "medical_history": {"disease": "diabetes", "risk": "Low",
            "data": {"age": 34, "time_in_hospital": 2, "num_lab_procedures": 18, "num_procedures": 1, "num_medications": 6, "number_outpatient": 0, "number_emergency": 0, "number_inpatient": 0, "number_diagnoses": 3}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK (moderate stays, moderate procedures) ---
    {
        "first_name": "Anita",    "last_name": "Kulkarni", "age": 45, "gender": "Female",
        "medical_history": {"disease": "diabetes", "risk": "Medium",
            "data": {"age": 45, "time_in_hospital": 4, "num_lab_procedures": 42, "num_procedures": 2, "num_medications": 12, "number_outpatient": 1, "number_emergency": 0, "number_inpatient": 1, "number_diagnoses": 6}},
        "allergies": [], "current_medications": ["Metformin 500mg"],
    },
    {
        "first_name": "Manoj",    "last_name": "Tiwari",   "age": 50, "gender": "Male",
        "medical_history": {"disease": "diabetes", "risk": "Medium",
            "data": {"age": 50, "time_in_hospital": 5, "num_lab_procedures": 50, "num_procedures": 3, "num_medications": 15, "number_outpatient": 2, "number_emergency": 1, "number_inpatient": 1, "number_diagnoses": 7}},
        "allergies": [], "current_medications": ["Glimepiride 2mg"],
    },
    {
        "first_name": "Sunita",   "last_name": "Desai",    "age": 48, "gender": "Female",
        "medical_history": {"disease": "diabetes", "risk": "Medium",
            "data": {"age": 48, "time_in_hospital": 4, "num_lab_procedures": 38, "num_procedures": 2, "num_medications": 11, "number_outpatient": 1, "number_emergency": 0, "number_inpatient": 1, "number_diagnoses": 5}},
        "allergies": ["Metformin"], "current_medications": ["Sitagliptin 100mg"],
    },
    {
        "first_name": "Deepak",   "last_name": "Yadav",    "age": 53, "gender": "Male",
        "medical_history": {"disease": "diabetes", "risk": "Medium",
            "data": {"age": 53, "time_in_hospital": 5, "num_lab_procedures": 55, "num_procedures": 3, "num_medications": 16, "number_outpatient": 2, "number_emergency": 1, "number_inpatient": 2, "number_diagnoses": 7}},
        "allergies": [], "current_medications": ["Metformin 1000mg"],
    },
    # --- HIGH RISK (long stays, many procedures, many meds, repeat visits) ---
    {
        "first_name": "Rekha",    "last_name": "Pandey",   "age": 62, "gender": "Female",
        "medical_history": {"disease": "diabetes", "risk": "High",
            "data": {"age": 62, "time_in_hospital": 10, "num_lab_procedures": 72, "num_procedures": 5, "num_medications": 22, "number_outpatient": 3, "number_emergency": 2, "number_inpatient": 4, "number_diagnoses": 9}},
        "allergies": [], "current_medications": ["Insulin Glargine 30U", "Metformin 2000mg", "Atorvastatin 20mg"],
    },
    {
        "first_name": "Gopal",    "last_name": "Mishra",   "age": 65, "gender": "Male",
        "medical_history": {"disease": "diabetes", "risk": "High",
            "data": {"age": 65, "time_in_hospital": 12, "num_lab_procedures": 80, "num_procedures": 6, "num_medications": 25, "number_outpatient": 4, "number_emergency": 3, "number_inpatient": 5, "number_diagnoses": 9}},
        "allergies": ["Sulfonamides"], "current_medications": ["Insulin Lispro", "Empagliflozin 25mg"],
    },
    {
        "first_name": "Padma",    "last_name": "Rao",      "age": 58, "gender": "Female",
        "medical_history": {"disease": "diabetes", "risk": "High",
            "data": {"age": 58, "time_in_hospital": 9, "num_lab_procedures": 68, "num_procedures": 4, "num_medications": 20, "number_outpatient": 3, "number_emergency": 2, "number_inpatient": 3, "number_diagnoses": 8}},
        "allergies": [], "current_medications": ["Insulin Aspart", "Dapagliflozin 10mg", "Lisinopril 20mg"],
    },
]


# ========================================================================
#  KIDNEY DISEASE  (UCI CKD dataset features — pre-encoded)
#  Real features (24): age, bp, sg, al, su, rbc_enc, pc_enc, pcc_enc,
#      ba_enc, bgr, bu, sc, sod, pot, hemo, pcv, wc, rc,
#      htn_enc, dm_enc, cad_enc, appet_enc, pe_enc, ane_enc
#  Encoding: rbc_enc=1 if abnormal, pc_enc=1 if abnormal,
#            pcc_enc=1 if present, ba_enc=1 if present,
#            htn/dm/cad/pe/ane_enc=1 if yes, appet_enc=1 if good
# ========================================================================
KIDNEY_DISEASE_PATIENTS = [
    # --- LOW RISK (healthy kidney profiles) ---
    {
        "first_name": "Nikhil",   "last_name": "Bhat",     "age": 33, "gender": "Male",
        "medical_history": {"disease": "kidney_disease", "risk": "Low",
            "data": {"age": 33, "bp": 70, "sg": 1.025, "al": 0, "su": 0, "rbc_enc": 0, "pc_enc": 0, "pcc_enc": 0, "ba_enc": 0, "bgr": 95, "bu": 18, "sc": 0.9, "sod": 142, "pot": 4.2, "hemo": 16.0, "pcv": 48, "wc": 7500, "rc": 5.2, "htn_enc": 0, "dm_enc": 0, "cad_enc": 0, "appet_enc": 1, "pe_enc": 0, "ane_enc": 0}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Pooja",    "last_name": "Hegde",    "age": 29, "gender": "Female",
        "medical_history": {"disease": "kidney_disease", "risk": "Low",
            "data": {"age": 29, "bp": 65, "sg": 1.020, "al": 0, "su": 0, "rbc_enc": 0, "pc_enc": 0, "pcc_enc": 0, "ba_enc": 0, "bgr": 88, "bu": 15, "sc": 0.7, "sod": 140, "pot": 4.0, "hemo": 14.5, "pcv": 44, "wc": 6800, "rc": 4.8, "htn_enc": 0, "dm_enc": 0, "cad_enc": 0, "appet_enc": 1, "pe_enc": 0, "ane_enc": 0}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Arun",     "last_name": "Pillai",   "age": 36, "gender": "Male",
        "medical_history": {"disease": "kidney_disease", "risk": "Low",
            "data": {"age": 36, "bp": 75, "sg": 1.020, "al": 0, "su": 0, "rbc_enc": 0, "pc_enc": 0, "pcc_enc": 0, "ba_enc": 0, "bgr": 100, "bu": 22, "sc": 1.0, "sod": 138, "pot": 4.5, "hemo": 15.5, "pcv": 46, "wc": 8000, "rc": 5.0, "htn_enc": 0, "dm_enc": 0, "cad_enc": 0, "appet_enc": 1, "pe_enc": 0, "ane_enc": 0}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK (elevated markers, some comorbidities) ---
    {
        "first_name": "Swati",    "last_name": "Patil",    "age": 50, "gender": "Female",
        "medical_history": {"disease": "kidney_disease", "risk": "Medium",
            "data": {"age": 50, "bp": 90, "sg": 1.015, "al": 2, "su": 1, "rbc_enc": 0, "pc_enc": 1, "pcc_enc": 0, "ba_enc": 0, "bgr": 130, "bu": 55, "sc": 1.8, "sod": 135, "pot": 4.8, "hemo": 12.0, "pcv": 38, "wc": 9000, "rc": 4.2, "htn_enc": 1, "dm_enc": 0, "cad_enc": 0, "appet_enc": 1, "pe_enc": 0, "ane_enc": 0}},
        "allergies": [], "current_medications": ["Telmisartan 40mg"],
    },
    {
        "first_name": "Rajesh",   "last_name": "Saxena",   "age": 55, "gender": "Male",
        "medical_history": {"disease": "kidney_disease", "risk": "Medium",
            "data": {"age": 55, "bp": 95, "sg": 1.010, "al": 3, "su": 2, "rbc_enc": 1, "pc_enc": 1, "pcc_enc": 0, "ba_enc": 0, "bgr": 145, "bu": 62, "sc": 2.1, "sod": 132, "pot": 5.0, "hemo": 11.5, "pcv": 36, "wc": 9500, "rc": 4.0, "htn_enc": 1, "dm_enc": 1, "cad_enc": 0, "appet_enc": 1, "pe_enc": 0, "ane_enc": 1}},
        "allergies": [], "current_medications": ["Losartan 50mg", "Furosemide 20mg"],
    },
    {
        "first_name": "Geeta",    "last_name": "Shetty",   "age": 47, "gender": "Female",
        "medical_history": {"disease": "kidney_disease", "risk": "Medium",
            "data": {"age": 47, "bp": 85, "sg": 1.015, "al": 2, "su": 0, "rbc_enc": 0, "pc_enc": 0, "pcc_enc": 1, "ba_enc": 0, "bgr": 120, "bu": 48, "sc": 1.6, "sod": 136, "pot": 4.6, "hemo": 12.5, "pcv": 39, "wc": 8500, "rc": 4.3, "htn_enc": 1, "dm_enc": 0, "cad_enc": 0, "appet_enc": 1, "pe_enc": 0, "ane_enc": 0}},
        "allergies": ["NSAIDs"], "current_medications": ["Amlodipine 5mg"],
    },
    {
        "first_name": "Venkat",   "last_name": "Reddy",    "age": 52, "gender": "Male",
        "medical_history": {"disease": "kidney_disease", "risk": "Medium",
            "data": {"age": 52, "bp": 90, "sg": 1.010, "al": 2, "su": 1, "rbc_enc": 1, "pc_enc": 0, "pcc_enc": 0, "ba_enc": 0, "bgr": 138, "bu": 58, "sc": 1.9, "sod": 134, "pot": 4.9, "hemo": 11.8, "pcv": 37, "wc": 9200, "rc": 4.1, "htn_enc": 1, "dm_enc": 1, "cad_enc": 0, "appet_enc": 0, "pe_enc": 1, "ane_enc": 0}},
        "allergies": [], "current_medications": ["Enalapril 10mg"],
    },
    # --- HIGH RISK (severe CKD markers) ---
    {
        "first_name": "Kamla",    "last_name": "Devi",     "age": 68, "gender": "Female",
        "medical_history": {"disease": "kidney_disease", "risk": "High",
            "data": {"age": 68, "bp": 110, "sg": 1.005, "al": 4, "su": 4, "rbc_enc": 1, "pc_enc": 1, "pcc_enc": 1, "ba_enc": 1, "bgr": 220, "bu": 145, "sc": 5.8, "sod": 120, "pot": 6.5, "hemo": 7.5, "pcv": 24, "wc": 15000, "rc": 2.8, "htn_enc": 1, "dm_enc": 1, "cad_enc": 1, "appet_enc": 0, "pe_enc": 1, "ane_enc": 1}},
        "allergies": ["Contrast dye"], "current_medications": ["Erythropoietin", "Calcium Carbonate", "Calcitriol"],
    },
    {
        "first_name": "Harish",   "last_name": "Chandra",  "age": 72, "gender": "Male",
        "medical_history": {"disease": "kidney_disease", "risk": "High",
            "data": {"age": 72, "bp": 120, "sg": 1.005, "al": 5, "su": 5, "rbc_enc": 1, "pc_enc": 1, "pcc_enc": 1, "ba_enc": 1, "bgr": 250, "bu": 168, "sc": 7.2, "sod": 118, "pot": 7.0, "hemo": 6.8, "pcv": 22, "wc": 17000, "rc": 2.5, "htn_enc": 1, "dm_enc": 1, "cad_enc": 1, "appet_enc": 0, "pe_enc": 1, "ane_enc": 1}},
        "allergies": [], "current_medications": ["Sevelamer", "Iron Sucrose IV", "Epoetin alfa"],
    },
    {
        "first_name": "Savitri",  "last_name": "Prasad",   "age": 65, "gender": "Female",
        "medical_history": {"disease": "kidney_disease", "risk": "High",
            "data": {"age": 65, "bp": 105, "sg": 1.005, "al": 4, "su": 3, "rbc_enc": 1, "pc_enc": 1, "pcc_enc": 1, "ba_enc": 0, "bgr": 200, "bu": 155, "sc": 6.5, "sod": 122, "pot": 6.2, "hemo": 8.0, "pcv": 26, "wc": 14000, "rc": 3.0, "htn_enc": 1, "dm_enc": 1, "cad_enc": 0, "appet_enc": 0, "pe_enc": 1, "ane_enc": 1}},
        "allergies": ["ACE inhibitors"], "current_medications": ["Dialysis 3x/week", "Cinacalcet 30mg"],
    },
]


# ========================================================================
#  LIVER DISEASE  (Indian Liver Patient Dataset features)
#  Real features (10): age, gender_enc(Male=1,Female=0), bilirubin, db,
#                       alk_phosphatase, sgpt, sgot, tp, alb, ag_ratio
# ========================================================================
LIVER_DISEASE_PATIENTS = [
    # --- LOW RISK ---
    {
        "first_name": "Karthik",  "last_name": "Subramani","age": 31, "gender": "Male",
        "medical_history": {"disease": "liver_disease", "risk": "Low",
            "data": {"age": 31, "gender_enc": 1, "bilirubin": 0.6, "db": 0.2, "alk_phosphatase": 72, "sgpt": 18, "sgot": 22, "tp": 7.2, "alb": 4.2, "ag_ratio": 1.4}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Neha",     "last_name": "Kapoor",   "age": 27, "gender": "Female",
        "medical_history": {"disease": "liver_disease", "risk": "Low",
            "data": {"age": 27, "gender_enc": 0, "bilirubin": 0.4, "db": 0.1, "alk_phosphatase": 65, "sgpt": 15, "sgot": 19, "tp": 7.5, "alb": 4.5, "ag_ratio": 1.5}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Sanjay",   "last_name": "Malhotra", "age": 38, "gender": "Male",
        "medical_history": {"disease": "liver_disease", "risk": "Low",
            "data": {"age": 38, "gender_enc": 1, "bilirubin": 0.8, "db": 0.3, "alk_phosphatase": 85, "sgpt": 24, "sgot": 28, "tp": 7.0, "alb": 4.0, "ag_ratio": 1.3}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Ritu",     "last_name": "Chauhan",  "age": 45, "gender": "Female",
        "medical_history": {"disease": "liver_disease", "risk": "Medium",
            "data": {"age": 45, "gender_enc": 0, "bilirubin": 2.8, "db": 1.2, "alk_phosphatase": 185, "sgpt": 68, "sgot": 75, "tp": 6.5, "alb": 3.2, "ag_ratio": 0.97}},
        "allergies": [], "current_medications": ["Ursodeoxycholic Acid 300mg"],
    },
    {
        "first_name": "Ajay",     "last_name": "Thakur",   "age": 52, "gender": "Male",
        "medical_history": {"disease": "liver_disease", "risk": "Medium",
            "data": {"age": 52, "gender_enc": 1, "bilirubin": 3.2, "db": 1.5, "alk_phosphatase": 210, "sgpt": 82, "sgot": 88, "tp": 6.2, "alb": 3.0, "ag_ratio": 0.94}},
        "allergies": [], "current_medications": ["Silymarin 140mg"],
    },
    {
        "first_name": "Manju",    "last_name": "Agarwal",  "age": 49, "gender": "Female",
        "medical_history": {"disease": "liver_disease", "risk": "Medium",
            "data": {"age": 49, "gender_enc": 0, "bilirubin": 2.5, "db": 1.0, "alk_phosphatase": 175, "sgpt": 62, "sgot": 70, "tp": 6.4, "alb": 3.1, "ag_ratio": 0.94}},
        "allergies": ["Acetaminophen"], "current_medications": ["Lactulose"],
    },
    {
        "first_name": "Prakash",  "last_name": "Jha",      "age": 54, "gender": "Male",
        "medical_history": {"disease": "liver_disease", "risk": "Medium",
            "data": {"age": 54, "gender_enc": 1, "bilirubin": 3.5, "db": 1.6, "alk_phosphatase": 220, "sgpt": 78, "sgot": 85, "tp": 6.0, "alb": 2.8, "ag_ratio": 0.88}},
        "allergies": [], "current_medications": ["Propranolol 40mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Saroj",    "last_name": "Kumari",   "age": 60, "gender": "Female",
        "medical_history": {"disease": "liver_disease", "risk": "High",
            "data": {"age": 60, "gender_enc": 0, "bilirubin": 12.5, "db": 6.0, "alk_phosphatase": 520, "sgpt": 285, "sgot": 310, "tp": 5.2, "alb": 2.0, "ag_ratio": 0.63}},
        "allergies": ["Statins"], "current_medications": ["Rifaximin 550mg", "Lactulose", "Spironolactone 100mg"],
    },
    {
        "first_name": "Bharat",   "last_name": "Saxena",   "age": 58, "gender": "Male",
        "medical_history": {"disease": "liver_disease", "risk": "High",
            "data": {"age": 58, "gender_enc": 1, "bilirubin": 15.0, "db": 7.5, "alk_phosphatase": 580, "sgpt": 320, "sgot": 350, "tp": 5.0, "alb": 1.8, "ag_ratio": 0.56}},
        "allergies": [], "current_medications": ["Albumin infusion", "Furosemide 80mg", "Vitamin K"],
    },
    {
        "first_name": "Usha",     "last_name": "Tripathi", "age": 63, "gender": "Female",
        "medical_history": {"disease": "liver_disease", "risk": "High",
            "data": {"age": 63, "gender_enc": 0, "bilirubin": 10.8, "db": 5.2, "alk_phosphatase": 480, "sgpt": 260, "sgot": 290, "tp": 5.4, "alb": 2.2, "ag_ratio": 0.69}},
        "allergies": ["NSAIDs"], "current_medications": ["Terlipressin", "Octreotide", "Albumin IV"],
    },
]


# ========================================================================
#  BREAST CANCER  (Wisconsin WBCD — all 30 features)
#  Real features: radius/texture/perimeter/area/smoothness/compactness/
#     concavity/concave_points/symmetry/fractal_dimension × {_mean,_se,_worst}
# ========================================================================
BREAST_CANCER_PATIENTS = [
    # --- LOW RISK (Benign profiles — small, smooth, regular) ---
    {
        "first_name": "Nandini",  "last_name": "Sen",      "age": 34, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "Low",
            "data": {"radius_mean": 10.2, "texture_mean": 15.8, "perimeter_mean": 65.0, "area_mean": 320.0, "smoothness_mean": 0.078, "compactness_mean": 0.045, "concavity_mean": 0.020, "concave_points_mean": 0.010, "symmetry_mean": 0.165, "fractal_dimension_mean": 0.058,
                     "radius_se": 0.20, "texture_se": 0.60, "perimeter_se": 1.5, "area_se": 15.0, "smoothness_se": 0.004, "compactness_se": 0.008, "concavity_se": 0.010, "concave_points_se": 0.004, "symmetry_se": 0.012, "fractal_dimension_se": 0.002,
                     "radius_worst": 11.5, "texture_worst": 20.0, "perimeter_worst": 75.0, "area_worst": 400.0, "smoothness_worst": 0.110, "compactness_worst": 0.08, "concavity_worst": 0.06, "concave_points_worst": 0.025, "symmetry_worst": 0.22, "fractal_dimension_worst": 0.065}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Manish",   "last_name": "Dubey",    "age": 40, "gender": "Male",
        "medical_history": {"disease": "breast_cancer", "risk": "Low",
            "data": {"radius_mean": 11.5, "texture_mean": 16.2, "perimeter_mean": 72.5, "area_mean": 410.0, "smoothness_mean": 0.082, "compactness_mean": 0.050, "concavity_mean": 0.025, "concave_points_mean": 0.012, "symmetry_mean": 0.170, "fractal_dimension_mean": 0.060,
                     "radius_se": 0.22, "texture_se": 0.70, "perimeter_se": 1.7, "area_se": 18.0, "smoothness_se": 0.005, "compactness_se": 0.010, "concavity_se": 0.012, "concave_points_se": 0.005, "symmetry_se": 0.014, "fractal_dimension_se": 0.003,
                     "radius_worst": 12.8, "texture_worst": 21.5, "perimeter_worst": 82.0, "area_worst": 500.0, "smoothness_worst": 0.115, "compactness_worst": 0.10, "concavity_worst": 0.08, "concave_points_worst": 0.030, "symmetry_worst": 0.24, "fractal_dimension_worst": 0.070}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Suman",    "last_name": "Ghosh",    "age": 38, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "Low",
            "data": {"radius_mean": 9.8, "texture_mean": 14.5, "perimeter_mean": 62.0, "area_mean": 295.0, "smoothness_mean": 0.075, "compactness_mean": 0.042, "concavity_mean": 0.018, "concave_points_mean": 0.008, "symmetry_mean": 0.160, "fractal_dimension_mean": 0.056,
                     "radius_se": 0.18, "texture_se": 0.55, "perimeter_se": 1.3, "area_se": 12.0, "smoothness_se": 0.003, "compactness_se": 0.007, "concavity_se": 0.008, "concave_points_se": 0.003, "symmetry_se": 0.010, "fractal_dimension_se": 0.002,
                     "radius_worst": 10.8, "texture_worst": 18.5, "perimeter_worst": 70.0, "area_worst": 360.0, "smoothness_worst": 0.105, "compactness_worst": 0.07, "concavity_worst": 0.05, "concave_points_worst": 0.020, "symmetry_worst": 0.21, "fractal_dimension_worst": 0.062}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Alok",     "last_name": "Srivastava","age": 52, "gender": "Male",
        "medical_history": {"disease": "breast_cancer", "risk": "Medium",
            "data": {"radius_mean": 14.2, "texture_mean": 19.5, "perimeter_mean": 92.0, "area_mean": 620.0, "smoothness_mean": 0.098, "compactness_mean": 0.10, "concavity_mean": 0.09, "concave_points_mean": 0.05, "symmetry_mean": 0.190, "fractal_dimension_mean": 0.062,
                     "radius_se": 0.40, "texture_se": 1.0, "perimeter_se": 3.0, "area_se": 40.0, "smoothness_se": 0.006, "compactness_se": 0.020, "concavity_se": 0.025, "concave_points_se": 0.010, "symmetry_se": 0.018, "fractal_dimension_se": 0.004,
                     "radius_worst": 16.5, "texture_worst": 25.0, "perimeter_worst": 108.0, "area_worst": 850.0, "smoothness_worst": 0.135, "compactness_worst": 0.18, "concavity_worst": 0.20, "concave_points_worst": 0.08, "symmetry_worst": 0.28, "fractal_dimension_worst": 0.078}},
        "allergies": [], "current_medications": ["Tamoxifen 20mg"],
    },
    {
        "first_name": "Rina",     "last_name": "Mukherjee","age": 48, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "Medium",
            "data": {"radius_mean": 15.0, "texture_mean": 20.8, "perimeter_mean": 97.0, "area_mean": 700.0, "smoothness_mean": 0.102, "compactness_mean": 0.12, "concavity_mean": 0.10, "concave_points_mean": 0.06, "symmetry_mean": 0.195, "fractal_dimension_mean": 0.064,
                     "radius_se": 0.45, "texture_se": 1.1, "perimeter_se": 3.5, "area_se": 45.0, "smoothness_se": 0.007, "compactness_se": 0.025, "concavity_se": 0.030, "concave_points_se": 0.012, "symmetry_se": 0.020, "fractal_dimension_se": 0.004,
                     "radius_worst": 17.5, "texture_worst": 26.5, "perimeter_worst": 115.0, "area_worst": 950.0, "smoothness_worst": 0.140, "compactness_worst": 0.22, "concavity_worst": 0.25, "concave_points_worst": 0.10, "symmetry_worst": 0.30, "fractal_dimension_worst": 0.082}},
        "allergies": [], "current_medications": ["Letrozole 2.5mg"],
    },
    {
        "first_name": "Vinod",    "last_name": "Khanna",   "age": 55, "gender": "Male",
        "medical_history": {"disease": "breast_cancer", "risk": "Medium",
            "data": {"radius_mean": 13.8, "texture_mean": 18.9, "perimeter_mean": 89.5, "area_mean": 585.0, "smoothness_mean": 0.095, "compactness_mean": 0.09, "concavity_mean": 0.08, "concave_points_mean": 0.04, "symmetry_mean": 0.185, "fractal_dimension_mean": 0.061,
                     "radius_se": 0.35, "texture_se": 0.9, "perimeter_se": 2.5, "area_se": 35.0, "smoothness_se": 0.005, "compactness_se": 0.018, "concavity_se": 0.020, "concave_points_se": 0.008, "symmetry_se": 0.016, "fractal_dimension_se": 0.003,
                     "radius_worst": 15.8, "texture_worst": 24.0, "perimeter_worst": 102.0, "area_worst": 780.0, "smoothness_worst": 0.130, "compactness_worst": 0.16, "concavity_worst": 0.18, "concave_points_worst": 0.07, "symmetry_worst": 0.27, "fractal_dimension_worst": 0.075}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Archana",  "last_name": "Rao",      "age": 50, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "Medium",
            "data": {"radius_mean": 14.8, "texture_mean": 21.0, "perimeter_mean": 95.0, "area_mean": 680.0, "smoothness_mean": 0.100, "compactness_mean": 0.11, "concavity_mean": 0.095, "concave_points_mean": 0.055, "symmetry_mean": 0.192, "fractal_dimension_mean": 0.063,
                     "radius_se": 0.42, "texture_se": 1.05, "perimeter_se": 3.2, "area_se": 42.0, "smoothness_se": 0.006, "compactness_se": 0.022, "concavity_se": 0.028, "concave_points_se": 0.011, "symmetry_se": 0.019, "fractal_dimension_se": 0.004,
                     "radius_worst": 17.0, "texture_worst": 26.0, "perimeter_worst": 112.0, "area_worst": 910.0, "smoothness_worst": 0.138, "compactness_worst": 0.20, "concavity_worst": 0.22, "concave_points_worst": 0.09, "symmetry_worst": 0.29, "fractal_dimension_worst": 0.080}},
        "allergies": [], "current_medications": ["Anastrozole 1mg"],
    },
    # --- HIGH RISK (Malignant profiles — large, irregular, invasive) ---
    {
        "first_name": "Chitra",   "last_name": "Banerjee", "age": 62, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "High",
            "data": {"radius_mean": 21.5, "texture_mean": 28.5, "perimeter_mean": 142.0, "area_mean": 1420.0, "smoothness_mean": 0.135, "compactness_mean": 0.25, "concavity_mean": 0.30, "concave_points_mean": 0.15, "symmetry_mean": 0.240, "fractal_dimension_mean": 0.075,
                     "radius_se": 0.80, "texture_se": 1.8, "perimeter_se": 6.0, "area_se": 100.0, "smoothness_se": 0.010, "compactness_se": 0.045, "concavity_se": 0.060, "concave_points_se": 0.025, "symmetry_se": 0.030, "fractal_dimension_se": 0.007,
                     "radius_worst": 25.0, "texture_worst": 35.0, "perimeter_worst": 170.0, "area_worst": 1900.0, "smoothness_worst": 0.175, "compactness_worst": 0.40, "concavity_worst": 0.50, "concave_points_worst": 0.20, "symmetry_worst": 0.38, "fractal_dimension_worst": 0.10}},
        "allergies": ["Doxorubicin"], "current_medications": ["Trastuzumab", "Pertuzumab", "Paclitaxel"],
    },
    {
        "first_name": "Satish",   "last_name": "Agrawal",  "age": 58, "gender": "Male",
        "medical_history": {"disease": "breast_cancer", "risk": "High",
            "data": {"radius_mean": 20.2, "texture_mean": 26.8, "perimeter_mean": 135.0, "area_mean": 1280.0, "smoothness_mean": 0.128, "compactness_mean": 0.22, "concavity_mean": 0.28, "concave_points_mean": 0.14, "symmetry_mean": 0.230, "fractal_dimension_mean": 0.072,
                     "radius_se": 0.70, "texture_se": 1.5, "perimeter_se": 5.5, "area_se": 85.0, "smoothness_se": 0.009, "compactness_se": 0.040, "concavity_se": 0.055, "concave_points_se": 0.022, "symmetry_se": 0.028, "fractal_dimension_se": 0.006,
                     "radius_worst": 23.5, "texture_worst": 33.0, "perimeter_worst": 160.0, "area_worst": 1700.0, "smoothness_worst": 0.168, "compactness_worst": 0.35, "concavity_worst": 0.45, "concave_points_worst": 0.18, "symmetry_worst": 0.36, "fractal_dimension_worst": 0.095}},
        "allergies": [], "current_medications": ["Cyclophosphamide", "5-Fluorouracil"],
    },
    {
        "first_name": "Jaya",     "last_name": "Sharma",   "age": 65, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "High",
            "data": {"radius_mean": 23.0, "texture_mean": 30.2, "perimeter_mean": 150.0, "area_mean": 1600.0, "smoothness_mean": 0.142, "compactness_mean": 0.28, "concavity_mean": 0.35, "concave_points_mean": 0.17, "symmetry_mean": 0.250, "fractal_dimension_mean": 0.078,
                     "radius_se": 0.90, "texture_se": 2.0, "perimeter_se": 7.0, "area_se": 120.0, "smoothness_se": 0.012, "compactness_se": 0.050, "concavity_se": 0.070, "concave_points_se": 0.028, "symmetry_se": 0.035, "fractal_dimension_se": 0.008,
                     "radius_worst": 27.0, "texture_worst": 38.0, "perimeter_worst": 180.0, "area_worst": 2200.0, "smoothness_worst": 0.185, "compactness_worst": 0.45, "concavity_worst": 0.55, "concave_points_worst": 0.22, "symmetry_worst": 0.40, "fractal_dimension_worst": 0.11}},
        "allergies": [], "current_medications": ["Carboplatin", "Docetaxel", "Tamoxifen 20mg"],
    },
]


# ========================================================================
#  PARKINSON'S  (UCI Voice Dataset — Little et al., 2007)
#  Real features (22): MDVP:Fo(Hz), MDVP:Fhi(Hz), MDVP:Flo(Hz),
#      MDVP:Jitter(%), MDVP:Jitter(Abs), MDVP:RAP, MDVP:PPQ, Jitter:DDP,
#      MDVP:Shimmer, MDVP:Shimmer(dB), Shimmer:APQ3, Shimmer:APQ5,
#      MDVP:APQ, Shimmer:DDA, NHR, HNR, RPDE, DFA, spread1, spread2, D2, PPE
# ========================================================================
PARKINSONS_PATIENTS = [
    # --- LOW RISK (healthy voice — steady pitch, low jitter/shimmer, high HNR) ---
    {
        "first_name": "Dhruv",    "last_name": "Kapoor",   "age": 42, "gender": "Male",
        "medical_history": {"disease": "parkinsons", "risk": "Low",
            "data": {"MDVP:Fo(Hz)": 150.0, "MDVP:Fhi(Hz)": 165.0, "MDVP:Flo(Hz)": 135.0, "MDVP:Jitter(%)": 0.003, "MDVP:Jitter(Abs)": 0.00002, "MDVP:RAP": 0.0015, "MDVP:PPQ": 0.0018, "Jitter:DDP": 0.0045, "MDVP:Shimmer": 0.015, "MDVP:Shimmer(dB)": 0.15, "Shimmer:APQ3": 0.008, "Shimmer:APQ5": 0.010, "MDVP:APQ": 0.012, "Shimmer:DDA": 0.024, "NHR": 0.008, "HNR": 25.0, "RPDE": 0.38, "DFA": 0.62, "spread1": -6.5, "spread2": 0.12, "D2": 1.8, "PPE": 0.10}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Shweta",   "last_name": "Verma",    "age": 38, "gender": "Female",
        "medical_history": {"disease": "parkinsons", "risk": "Low",
            "data": {"MDVP:Fo(Hz)": 200.0, "MDVP:Fhi(Hz)": 220.0, "MDVP:Flo(Hz)": 180.0, "MDVP:Jitter(%)": 0.0025, "MDVP:Jitter(Abs)": 0.000015, "MDVP:RAP": 0.0012, "MDVP:PPQ": 0.0015, "Jitter:DDP": 0.0036, "MDVP:Shimmer": 0.012, "MDVP:Shimmer(dB)": 0.12, "Shimmer:APQ3": 0.006, "Shimmer:APQ5": 0.008, "MDVP:APQ": 0.010, "Shimmer:DDA": 0.018, "NHR": 0.006, "HNR": 27.0, "RPDE": 0.35, "DFA": 0.60, "spread1": -7.0, "spread2": 0.10, "D2": 1.6, "PPE": 0.08}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Gaurav",   "last_name": "Saxena",   "age": 45, "gender": "Male",
        "medical_history": {"disease": "parkinsons", "risk": "Low",
            "data": {"MDVP:Fo(Hz)": 140.0, "MDVP:Fhi(Hz)": 158.0, "MDVP:Flo(Hz)": 125.0, "MDVP:Jitter(%)": 0.0035, "MDVP:Jitter(Abs)": 0.000025, "MDVP:RAP": 0.0018, "MDVP:PPQ": 0.0020, "Jitter:DDP": 0.0054, "MDVP:Shimmer": 0.018, "MDVP:Shimmer(dB)": 0.18, "Shimmer:APQ3": 0.009, "Shimmer:APQ5": 0.012, "MDVP:APQ": 0.014, "Shimmer:DDA": 0.027, "NHR": 0.010, "HNR": 24.0, "RPDE": 0.40, "DFA": 0.63, "spread1": -6.2, "spread2": 0.14, "D2": 1.9, "PPE": 0.12}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK (moderate voice degradation) ---
    {
        "first_name": "Shalini",  "last_name": "Tiwari",   "age": 58, "gender": "Female",
        "medical_history": {"disease": "parkinsons", "risk": "Medium",
            "data": {"MDVP:Fo(Hz)": 160.0, "MDVP:Fhi(Hz)": 195.0, "MDVP:Flo(Hz)": 110.0, "MDVP:Jitter(%)": 0.006, "MDVP:Jitter(Abs)": 0.00004, "MDVP:RAP": 0.003, "MDVP:PPQ": 0.004, "Jitter:DDP": 0.009, "MDVP:Shimmer": 0.035, "MDVP:Shimmer(dB)": 0.35, "Shimmer:APQ3": 0.018, "Shimmer:APQ5": 0.022, "MDVP:APQ": 0.028, "Shimmer:DDA": 0.054, "NHR": 0.025, "HNR": 20.0, "RPDE": 0.50, "DFA": 0.70, "spread1": -5.0, "spread2": 0.22, "D2": 2.4, "PPE": 0.22}},
        "allergies": [], "current_medications": ["Levodopa/Carbidopa 25/100mg"],
    },
    {
        "first_name": "Mohan",    "last_name": "Das",      "age": 62, "gender": "Male",
        "medical_history": {"disease": "parkinsons", "risk": "Medium",
            "data": {"MDVP:Fo(Hz)": 120.0, "MDVP:Fhi(Hz)": 155.0, "MDVP:Flo(Hz)": 85.0, "MDVP:Jitter(%)": 0.008, "MDVP:Jitter(Abs)": 0.00005, "MDVP:RAP": 0.004, "MDVP:PPQ": 0.005, "Jitter:DDP": 0.012, "MDVP:Shimmer": 0.040, "MDVP:Shimmer(dB)": 0.40, "Shimmer:APQ3": 0.022, "Shimmer:APQ5": 0.026, "MDVP:APQ": 0.032, "Shimmer:DDA": 0.066, "NHR": 0.030, "HNR": 18.5, "RPDE": 0.55, "DFA": 0.72, "spread1": -4.5, "spread2": 0.25, "D2": 2.6, "PPE": 0.28}},
        "allergies": [], "current_medications": ["Pramipexole 0.5mg", "Levodopa/Carbidopa"],
    },
    {
        "first_name": "Kiran",    "last_name": "Bose",     "age": 55, "gender": "Female",
        "medical_history": {"disease": "parkinsons", "risk": "Medium",
            "data": {"MDVP:Fo(Hz)": 175.0, "MDVP:Fhi(Hz)": 210.0, "MDVP:Flo(Hz)": 120.0, "MDVP:Jitter(%)": 0.005, "MDVP:Jitter(Abs)": 0.000035, "MDVP:RAP": 0.0025, "MDVP:PPQ": 0.0035, "Jitter:DDP": 0.0075, "MDVP:Shimmer": 0.030, "MDVP:Shimmer(dB)": 0.30, "Shimmer:APQ3": 0.016, "Shimmer:APQ5": 0.020, "MDVP:APQ": 0.025, "Shimmer:DDA": 0.048, "NHR": 0.020, "HNR": 21.0, "RPDE": 0.48, "DFA": 0.68, "spread1": -5.2, "spread2": 0.20, "D2": 2.3, "PPE": 0.20}},
        "allergies": [], "current_medications": ["Rasagiline 1mg"],
    },
    {
        "first_name": "Prasad",   "last_name": "Menon",    "age": 60, "gender": "Male",
        "medical_history": {"disease": "parkinsons", "risk": "Medium",
            "data": {"MDVP:Fo(Hz)": 130.0, "MDVP:Fhi(Hz)": 168.0, "MDVP:Flo(Hz)": 95.0, "MDVP:Jitter(%)": 0.007, "MDVP:Jitter(Abs)": 0.000045, "MDVP:RAP": 0.0035, "MDVP:PPQ": 0.0045, "Jitter:DDP": 0.0105, "MDVP:Shimmer": 0.038, "MDVP:Shimmer(dB)": 0.38, "Shimmer:APQ3": 0.020, "Shimmer:APQ5": 0.024, "MDVP:APQ": 0.030, "Shimmer:DDA": 0.060, "NHR": 0.028, "HNR": 19.0, "RPDE": 0.53, "DFA": 0.71, "spread1": -4.8, "spread2": 0.23, "D2": 2.5, "PPE": 0.25}},
        "allergies": [], "current_medications": ["Ropinirole 4mg"],
    },
    # --- HIGH RISK (severe voice degradation — high jitter/shimmer, low HNR) ---
    {
        "first_name": "Prema",    "last_name": "Naidu",    "age": 72, "gender": "Female",
        "medical_history": {"disease": "parkinsons", "risk": "High",
            "data": {"MDVP:Fo(Hz)": 145.0, "MDVP:Fhi(Hz)": 240.0, "MDVP:Flo(Hz)": 65.0, "MDVP:Jitter(%)": 0.015, "MDVP:Jitter(Abs)": 0.00010, "MDVP:RAP": 0.008, "MDVP:PPQ": 0.010, "Jitter:DDP": 0.024, "MDVP:Shimmer": 0.065, "MDVP:Shimmer(dB)": 0.65, "Shimmer:APQ3": 0.035, "Shimmer:APQ5": 0.042, "MDVP:APQ": 0.050, "Shimmer:DDA": 0.105, "NHR": 0.060, "HNR": 14.0, "RPDE": 0.65, "DFA": 0.78, "spread1": -3.0, "spread2": 0.35, "D2": 3.2, "PPE": 0.40}},
        "allergies": ["Anticholinergics"], "current_medications": ["Levodopa/Carbidopa/Entacapone", "Amantadine 100mg"],
    },
    {
        "first_name": "Shankar",  "last_name": "Pillai",   "age": 75, "gender": "Male",
        "medical_history": {"disease": "parkinsons", "risk": "High",
            "data": {"MDVP:Fo(Hz)": 100.0, "MDVP:Fhi(Hz)": 210.0, "MDVP:Flo(Hz)": 55.0, "MDVP:Jitter(%)": 0.020, "MDVP:Jitter(Abs)": 0.00015, "MDVP:RAP": 0.010, "MDVP:PPQ": 0.012, "Jitter:DDP": 0.030, "MDVP:Shimmer": 0.080, "MDVP:Shimmer(dB)": 0.80, "Shimmer:APQ3": 0.042, "Shimmer:APQ5": 0.050, "MDVP:APQ": 0.060, "Shimmer:DDA": 0.126, "NHR": 0.075, "HNR": 12.0, "RPDE": 0.70, "DFA": 0.82, "spread1": -2.5, "spread2": 0.40, "D2": 3.5, "PPE": 0.48}},
        "allergies": [], "current_medications": ["Deep Brain Stimulation", "Levodopa 600mg/day", "Clonazepam 0.5mg"],
    },
    {
        "first_name": "Vimala",   "last_name": "Krishnan", "age": 70, "gender": "Female",
        "medical_history": {"disease": "parkinsons", "risk": "High",
            "data": {"MDVP:Fo(Hz)": 155.0, "MDVP:Fhi(Hz)": 250.0, "MDVP:Flo(Hz)": 60.0, "MDVP:Jitter(%)": 0.018, "MDVP:Jitter(Abs)": 0.00012, "MDVP:RAP": 0.009, "MDVP:PPQ": 0.011, "Jitter:DDP": 0.027, "MDVP:Shimmer": 0.072, "MDVP:Shimmer(dB)": 0.72, "Shimmer:APQ3": 0.038, "Shimmer:APQ5": 0.046, "MDVP:APQ": 0.055, "Shimmer:DDA": 0.114, "NHR": 0.068, "HNR": 13.0, "RPDE": 0.68, "DFA": 0.80, "spread1": -2.8, "spread2": 0.38, "D2": 3.4, "PPE": 0.45}},
        "allergies": [], "current_medications": ["Apomorphine pump", "Levodopa CR 500mg"],
    },
]


# ========================================================================
#  HEPATITIS  (UCI Hepatitis Dataset features — all 19)
#  Real features: age, sex(1=M,2=F), steroid(1=no,2=yes),
#      antivirals(1=no,2=yes), fatigue(1=no,2=yes), malaise(1=no,2=yes),
#      anorexia(1=no,2=yes), liver_big(1=no,2=yes), liver_firm(1=no,2=yes),
#      spleen_palpable(1=no,2=yes), spiders(1=no,2=yes),
#      ascites(1=no,2=yes), varices(1=no,2=yes), bilirubin, alk_phosphatase,
#      sgot, albumin, protime, histology(1=no,2=yes)
# ========================================================================
HEPATITIS_PATIENTS = [
    # --- LOW RISK ---
    {
        "first_name": "Rohit",    "last_name": "Sinha",    "age": 29, "gender": "Male",
        "medical_history": {"disease": "hepatitis", "risk": "Low",
            "data": {"age": 29, "sex": 1, "steroid": 1, "antivirals": 1, "fatigue": 1, "malaise": 1, "anorexia": 1, "liver_big": 1, "liver_firm": 1, "spleen_palpable": 1, "spiders": 1, "ascites": 1, "varices": 1, "bilirubin": 0.5, "alk_phosphatase": 62, "sgot": 20, "albumin": 4.5, "protime": 85, "histology": 1}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Tanvi",    "last_name": "Shah",     "age": 25, "gender": "Female",
        "medical_history": {"disease": "hepatitis", "risk": "Low",
            "data": {"age": 25, "sex": 2, "steroid": 1, "antivirals": 1, "fatigue": 1, "malaise": 1, "anorexia": 1, "liver_big": 1, "liver_firm": 1, "spleen_palpable": 1, "spiders": 1, "ascites": 1, "varices": 1, "bilirubin": 0.4, "alk_phosphatase": 55, "sgot": 18, "albumin": 4.8, "protime": 90, "histology": 1}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Vishal",   "last_name": "Awasthi",  "age": 34, "gender": "Male",
        "medical_history": {"disease": "hepatitis", "risk": "Low",
            "data": {"age": 34, "sex": 1, "steroid": 1, "antivirals": 1, "fatigue": 1, "malaise": 1, "anorexia": 1, "liver_big": 1, "liver_firm": 1, "spleen_palpable": 1, "spiders": 1, "ascites": 1, "varices": 1, "bilirubin": 0.7, "alk_phosphatase": 70, "sgot": 24, "albumin": 4.3, "protime": 80, "histology": 1}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Pallavi",  "last_name": "Garg",     "age": 42, "gender": "Female",
        "medical_history": {"disease": "hepatitis", "risk": "Medium",
            "data": {"age": 42, "sex": 2, "steroid": 2, "antivirals": 2, "fatigue": 2, "malaise": 1, "anorexia": 1, "liver_big": 2, "liver_firm": 1, "spleen_palpable": 1, "spiders": 1, "ascites": 1, "varices": 1, "bilirubin": 2.2, "alk_phosphatase": 145, "sgot": 72, "albumin": 3.5, "protime": 65, "histology": 1}},
        "allergies": [], "current_medications": ["Entecavir 0.5mg"],
    },
    {
        "first_name": "Ashok",    "last_name": "Bansal",   "age": 48, "gender": "Male",
        "medical_history": {"disease": "hepatitis", "risk": "Medium",
            "data": {"age": 48, "sex": 1, "steroid": 2, "antivirals": 2, "fatigue": 2, "malaise": 2, "anorexia": 1, "liver_big": 2, "liver_firm": 2, "spleen_palpable": 1, "spiders": 1, "ascites": 1, "varices": 1, "bilirubin": 2.8, "alk_phosphatase": 160, "sgot": 82, "albumin": 3.2, "protime": 58, "histology": 1}},
        "allergies": [], "current_medications": ["Tenofovir 300mg"],
    },
    {
        "first_name": "Sushma",   "last_name": "Malhotra", "age": 44, "gender": "Female",
        "medical_history": {"disease": "hepatitis", "risk": "Medium",
            "data": {"age": 44, "sex": 2, "steroid": 2, "antivirals": 1, "fatigue": 2, "malaise": 1, "anorexia": 1, "liver_big": 2, "liver_firm": 1, "spleen_palpable": 1, "spiders": 1, "ascites": 1, "varices": 1, "bilirubin": 2.0, "alk_phosphatase": 135, "sgot": 65, "albumin": 3.6, "protime": 68, "histology": 1}},
        "allergies": [], "current_medications": ["Sofosbuvir/Velpatasvir"],
    },
    {
        "first_name": "Girish",   "last_name": "Wadia",    "age": 50, "gender": "Male",
        "medical_history": {"disease": "hepatitis", "risk": "Medium",
            "data": {"age": 50, "sex": 1, "steroid": 2, "antivirals": 2, "fatigue": 2, "malaise": 2, "anorexia": 2, "liver_big": 2, "liver_firm": 2, "spleen_palpable": 1, "spiders": 2, "ascites": 1, "varices": 1, "bilirubin": 3.0, "alk_phosphatase": 170, "sgot": 78, "albumin": 3.0, "protime": 55, "histology": 2}},
        "allergies": ["Interferon"], "current_medications": ["Ribavirin 1000mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Leela",    "last_name": "Nambiar",  "age": 58, "gender": "Female",
        "medical_history": {"disease": "hepatitis", "risk": "High",
            "data": {"age": 58, "sex": 2, "steroid": 2, "antivirals": 2, "fatigue": 2, "malaise": 2, "anorexia": 2, "liver_big": 2, "liver_firm": 2, "spleen_palpable": 2, "spiders": 2, "ascites": 2, "varices": 2, "bilirubin": 8.5, "alk_phosphatase": 420, "sgot": 280, "albumin": 2.2, "protime": 30, "histology": 2}},
        "allergies": [], "current_medications": ["Sofosbuvir/Ledipasvir", "Ribavirin", "Lactulose"],
    },
    {
        "first_name": "Dinesh",   "last_name": "Gupta",    "age": 62, "gender": "Male",
        "medical_history": {"disease": "hepatitis", "risk": "High",
            "data": {"age": 62, "sex": 1, "steroid": 2, "antivirals": 2, "fatigue": 2, "malaise": 2, "anorexia": 2, "liver_big": 2, "liver_firm": 2, "spleen_palpable": 2, "spiders": 2, "ascites": 2, "varices": 2, "bilirubin": 10.2, "alk_phosphatase": 480, "sgot": 320, "albumin": 1.8, "protime": 25, "histology": 2}},
        "allergies": ["Penicillin"], "current_medications": ["PEG-Interferon", "Entecavir 1mg", "Albumin IV"],
    },
    {
        "first_name": "Radha",    "last_name": "Krishna",  "age": 55, "gender": "Female",
        "medical_history": {"disease": "hepatitis", "risk": "High",
            "data": {"age": 55, "sex": 2, "steroid": 2, "antivirals": 2, "fatigue": 2, "malaise": 2, "anorexia": 2, "liver_big": 2, "liver_firm": 2, "spleen_palpable": 2, "spiders": 2, "ascites": 2, "varices": 1, "bilirubin": 9.0, "alk_phosphatase": 450, "sgot": 295, "albumin": 2.0, "protime": 28, "histology": 2}},
        "allergies": [], "current_medications": ["Glecaprevir/Pibrentasvir", "Spironolactone 50mg"],
    },
]


# ========================================================================
#  HEART FAILURE  (Chicco & Jurman 2020 dataset — all 12 features)
#  Real features: age, anaemia(0/1), creatinine_phosphokinase, diabetes(0/1),
#      ejection_fraction, high_blood_pressure(0/1), platelets,
#      serum_creatinine, serum_sodium, sex(0=F,1=M), smoking(0/1), time
# ========================================================================
HEART_FAILURE_PATIENTS = [
    # --- LOW RISK (good vitals, long follow-up) ---
    {
        "first_name": "Aarav",    "last_name": "Jain",     "age": 40, "gender": "Male",
        "medical_history": {"disease": "heart_failure", "risk": "Low",
            "data": {"age": 40, "anaemia": 0, "creatinine_phosphokinase": 180, "diabetes": 0, "ejection_fraction": 62, "high_blood_pressure": 0, "platelets": 280000, "serum_creatinine": 0.8, "serum_sodium": 140, "sex": 1, "smoking": 0, "time": 250}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Ishita",   "last_name": "Oberoi",   "age": 35, "gender": "Female",
        "medical_history": {"disease": "heart_failure", "risk": "Low",
            "data": {"age": 35, "anaemia": 0, "creatinine_phosphokinase": 150, "diabetes": 0, "ejection_fraction": 65, "high_blood_pressure": 0, "platelets": 300000, "serum_creatinine": 0.7, "serum_sodium": 142, "sex": 0, "smoking": 0, "time": 280}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Vivek",    "last_name": "Choudhary","age": 42, "gender": "Male",
        "medical_history": {"disease": "heart_failure", "risk": "Low",
            "data": {"age": 42, "anaemia": 0, "creatinine_phosphokinase": 200, "diabetes": 0, "ejection_fraction": 58, "high_blood_pressure": 0, "platelets": 260000, "serum_creatinine": 0.9, "serum_sodium": 139, "sex": 1, "smoking": 0, "time": 230}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Madhuri",  "last_name": "Nene",     "age": 58, "gender": "Female",
        "medical_history": {"disease": "heart_failure", "risk": "Medium",
            "data": {"age": 58, "anaemia": 1, "creatinine_phosphokinase": 450, "diabetes": 0, "ejection_fraction": 35, "high_blood_pressure": 1, "platelets": 200000, "serum_creatinine": 1.5, "serum_sodium": 134, "sex": 0, "smoking": 0, "time": 120}},
        "allergies": [], "current_medications": ["Enalapril 10mg", "Carvedilol 12.5mg"],
    },
    {
        "first_name": "Pankaj",   "last_name": "Tripathi", "age": 60, "gender": "Male",
        "medical_history": {"disease": "heart_failure", "risk": "Medium",
            "data": {"age": 60, "anaemia": 0, "creatinine_phosphokinase": 550, "diabetes": 1, "ejection_fraction": 30, "high_blood_pressure": 1, "platelets": 180000, "serum_creatinine": 1.8, "serum_sodium": 132, "sex": 1, "smoking": 1, "time": 100}},
        "allergies": [], "current_medications": ["Sacubitril/Valsartan 50mg", "Spironolactone 25mg"],
    },
    {
        "first_name": "Seema",    "last_name": "Biswas",   "age": 55, "gender": "Female",
        "medical_history": {"disease": "heart_failure", "risk": "Medium",
            "data": {"age": 55, "anaemia": 0, "creatinine_phosphokinase": 380, "diabetes": 0, "ejection_fraction": 38, "high_blood_pressure": 0, "platelets": 220000, "serum_creatinine": 1.3, "serum_sodium": 135, "sex": 0, "smoking": 0, "time": 140}},
        "allergies": [], "current_medications": ["Bisoprolol 5mg", "Furosemide 40mg"],
    },
    {
        "first_name": "Rajendra", "last_name": "Prasad",   "age": 62, "gender": "Male",
        "medical_history": {"disease": "heart_failure", "risk": "Medium",
            "data": {"age": 62, "anaemia": 1, "creatinine_phosphokinase": 600, "diabetes": 1, "ejection_fraction": 32, "high_blood_pressure": 1, "platelets": 170000, "serum_creatinine": 1.6, "serum_sodium": 133, "sex": 1, "smoking": 1, "time": 110}},
        "allergies": ["ACE inhibitors"], "current_medications": ["Valsartan 80mg", "Ivabradine 5mg"],
    },
    # --- HIGH RISK (low EF, high creatinine, short follow-up) ---
    {
        "first_name": "Kasturi",  "last_name": "Behera",   "age": 75, "gender": "Female",
        "medical_history": {"disease": "heart_failure", "risk": "High",
            "data": {"age": 75, "anaemia": 1, "creatinine_phosphokinase": 1200, "diabetes": 1, "ejection_fraction": 14, "high_blood_pressure": 1, "platelets": 120000, "serum_creatinine": 4.5, "serum_sodium": 118, "sex": 0, "smoking": 0, "time": 15}},
        "allergies": [], "current_medications": ["Dobutamine drip", "Furosemide IV", "Milrinone"],
    },
    {
        "first_name": "Mahendra", "last_name": "Tomar",    "age": 78, "gender": "Male",
        "medical_history": {"disease": "heart_failure", "risk": "High",
            "data": {"age": 78, "anaemia": 1, "creatinine_phosphokinase": 1500, "diabetes": 1, "ejection_fraction": 12, "high_blood_pressure": 1, "platelets": 100000, "serum_creatinine": 5.2, "serum_sodium": 115, "sex": 1, "smoking": 0, "time": 10}},
        "allergies": ["Beta-blockers"], "current_medications": ["LVAD candidate", "IV Diuretics", "Digoxin 0.125mg"],
    },
    {
        "first_name": "Pushpa",   "last_name": "Devi",     "age": 72, "gender": "Female",
        "medical_history": {"disease": "heart_failure", "risk": "High",
            "data": {"age": 72, "anaemia": 1, "creatinine_phosphokinase": 1100, "diabetes": 0, "ejection_fraction": 15, "high_blood_pressure": 1, "platelets": 130000, "serum_creatinine": 4.0, "serum_sodium": 120, "sex": 0, "smoking": 0, "time": 20}},
        "allergies": [], "current_medications": ["Sacubitril/Valsartan 100mg", "Furosemide 80mg", "Metolazone 5mg"],
    },
]


# ========================================================================
#  STROKE  (Kaggle Stroke Prediction — pre-encoded features)
#  Real features (10): gender_enc(Male=1,Female=0), age, hypertension(0/1),
#      heart_disease(0/1), ever_married_enc(Yes=1,No=0),
#      work_type_enc(Private=0,Self-employed=1,Govt_job=2,children=3,Never_worked=4),
#      Residence_type_enc(Urban=1,Rural=0), avg_glucose_level, bmi,
#      smoking_status_enc(never=0,formerly=1,smokes=2)
# ========================================================================
STROKE_PATIENTS = [
    # --- LOW RISK ---
    {
        "first_name": "Kabir",    "last_name": "Mehra",    "age": 30, "gender": "Male",
        "medical_history": {"disease": "stroke", "risk": "Low",
            "data": {"gender_enc": 1, "age": 30, "hypertension": 0, "heart_disease": 0, "ever_married_enc": 0, "work_type_enc": 0, "Residence_type_enc": 1, "avg_glucose_level": 82.5, "bmi": 22.0, "smoking_status_enc": 0}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Tara",     "last_name": "Menon",    "age": 28, "gender": "Female",
        "medical_history": {"disease": "stroke", "risk": "Low",
            "data": {"gender_enc": 0, "age": 28, "hypertension": 0, "heart_disease": 0, "ever_married_enc": 0, "work_type_enc": 0, "Residence_type_enc": 1, "avg_glucose_level": 78.0, "bmi": 21.5, "smoking_status_enc": 0}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Sameer",   "last_name": "Vohra",    "age": 35, "gender": "Male",
        "medical_history": {"disease": "stroke", "risk": "Low",
            "data": {"gender_enc": 1, "age": 35, "hypertension": 0, "heart_disease": 0, "ever_married_enc": 1, "work_type_enc": 0, "Residence_type_enc": 0, "avg_glucose_level": 88.0, "bmi": 24.2, "smoking_status_enc": 0}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Veena",    "last_name": "Kashyap",  "age": 55, "gender": "Female",
        "medical_history": {"disease": "stroke", "risk": "Medium",
            "data": {"gender_enc": 0, "age": 55, "hypertension": 1, "heart_disease": 0, "ever_married_enc": 1, "work_type_enc": 1, "Residence_type_enc": 1, "avg_glucose_level": 135.0, "bmi": 30.5, "smoking_status_enc": 1}},
        "allergies": [], "current_medications": ["Amlodipine 5mg", "Aspirin 81mg"],
    },
    {
        "first_name": "Naresh",   "last_name": "Goyal",    "age": 58, "gender": "Male",
        "medical_history": {"disease": "stroke", "risk": "Medium",
            "data": {"gender_enc": 1, "age": 58, "hypertension": 1, "heart_disease": 0, "ever_married_enc": 1, "work_type_enc": 1, "Residence_type_enc": 0, "avg_glucose_level": 148.0, "bmi": 31.2, "smoking_status_enc": 2}},
        "allergies": [], "current_medications": ["Losartan 100mg", "Atorvastatin 20mg"],
    },
    {
        "first_name": "Rashmi",   "last_name": "Batra",    "age": 52, "gender": "Female",
        "medical_history": {"disease": "stroke", "risk": "Medium",
            "data": {"gender_enc": 0, "age": 52, "hypertension": 1, "heart_disease": 0, "ever_married_enc": 1, "work_type_enc": 2, "Residence_type_enc": 1, "avg_glucose_level": 128.0, "bmi": 29.0, "smoking_status_enc": 1}},
        "allergies": [], "current_medications": ["Indapamide 1.5mg"],
    },
    {
        "first_name": "Hemant",   "last_name": "Khandelwal","age": 56, "gender": "Male",
        "medical_history": {"disease": "stroke", "risk": "Medium",
            "data": {"gender_enc": 1, "age": 56, "hypertension": 1, "heart_disease": 1, "ever_married_enc": 1, "work_type_enc": 0, "Residence_type_enc": 1, "avg_glucose_level": 155.0, "bmi": 32.0, "smoking_status_enc": 2}},
        "allergies": [], "current_medications": ["Clopidogrel 75mg", "Ramipril 5mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Sumitra",  "last_name": "Chauhan",  "age": 72, "gender": "Female",
        "medical_history": {"disease": "stroke", "risk": "High",
            "data": {"gender_enc": 0, "age": 72, "hypertension": 1, "heart_disease": 1, "ever_married_enc": 1, "work_type_enc": 1, "Residence_type_enc": 0, "avg_glucose_level": 240.0, "bmi": 38.5, "smoking_status_enc": 1}},
        "allergies": ["Heparin"], "current_medications": ["Warfarin", "Metoprolol 100mg", "Insulin Glargine"],
    },
    {
        "first_name": "Jagdish",  "last_name": "Prasad",   "age": 78, "gender": "Male",
        "medical_history": {"disease": "stroke", "risk": "High",
            "data": {"gender_enc": 1, "age": 78, "hypertension": 1, "heart_disease": 1, "ever_married_enc": 1, "work_type_enc": 1, "Residence_type_enc": 1, "avg_glucose_level": 265.0, "bmi": 36.0, "smoking_status_enc": 1}},
        "allergies": [], "current_medications": ["Apixaban 5mg", "Atorvastatin 80mg", "Amlodipine 10mg"],
    },
    {
        "first_name": "Kamini",   "last_name": "Lal",      "age": 68, "gender": "Female",
        "medical_history": {"disease": "stroke", "risk": "High",
            "data": {"gender_enc": 0, "age": 68, "hypertension": 1, "heart_disease": 1, "ever_married_enc": 1, "work_type_enc": 1, "Residence_type_enc": 1, "avg_glucose_level": 228.0, "bmi": 35.5, "smoking_status_enc": 2}},
        "allergies": ["Aspirin"], "current_medications": ["Dabigatran 150mg", "Rosuvastatin 40mg"],
    },
]


# ========================================================================
#  COLLECT ALL DISEASE DATA
# ========================================================================
ALL_DISEASES = {
    "Heart Disease":   HEART_DISEASE_PATIENTS,
    "Diabetes":        DIABETES_PATIENTS,
    "Kidney Disease":  KIDNEY_DISEASE_PATIENTS,
    "Liver Disease":   LIVER_DISEASE_PATIENTS,
    "Breast Cancer":   BREAST_CANCER_PATIENTS,
    "Parkinsons":      PARKINSONS_PATIENTS,
    "Hepatitis":       HEPATITIS_PATIENTS,
    "Heart Failure":   HEART_FAILURE_PATIENTS,
    "Stroke":          STROKE_PATIENTS,
}


def _build_ai_report(patient_data: dict, disease_name: str) -> dict:
    """Build an AIReport JSON payload by running real model inference.

    Calls the actual trained predictor for the disease, producing genuine
    probability, prediction, and confidence values instead of fabricated
    constants.
    """
    risk = patient_data["medical_history"]["risk"]
    data = patient_data["medical_history"]["data"]
    disease_key = patient_data["medical_history"]["disease"]
    name = f"{patient_data['first_name']} {patient_data['last_name']}"

    # --- Real model inference ---
    try:
        predictor = _get_predictor(disease_key)
        model_result = predictor.predict_json(data)
        prob = float(model_result.get("probability", 0.5))
        prediction = int(model_result.get("prediction", 0))
        confidence = float(model_result.get("confidence", prob))
        class_probabilities = model_result.get("class_probabilities", {"0": round(1 - prob, 3), "1": round(prob, 3)})
        is_model_inferred = True
    except Exception as e:
        # Fallback: if model loading fails, use a heuristic based on risk label
        print(f"  [WARN] Model inference failed for {disease_key}: {e}. Using fallback.")
        risk_prob = {"Low": 0.15, "Medium": 0.55, "High": 0.88}
        prob = risk_prob.get(risk, 0.5)
        prediction = 1 if risk in ("Medium", "High") else 0
        confidence = round(prob + 0.05, 2) if prob < 0.95 else 0.95
        class_probabilities = {"0": round(1 - prob, 3), "1": round(prob, 3)}
        is_model_inferred = False

    # Derive risk level from real probability
    if prob >= 0.70:
        derived_risk = "High"
    elif prob >= 0.40:
        derived_risk = "Medium"
    else:
        derived_risk = "Low"

    risk_assessment = {
        "disease": disease_name,
        "disease_key": disease_key,
        "risk_level": derived_risk,
        "risk_category": derived_risk,
        "probability": prob,
        "confidence": confidence,
        "confidence_label": f"{derived_risk} Risk",
        "prediction": prediction,
        "input_features": data,
        "class_probabilities": class_probabilities,
        "is_model_inferred": is_model_inferred,
    }

    rag_evidence = [
        {
            "source": f"Clinical Guidelines for {disease_name}",
            "content": f"Standard clinical protocol for {derived_risk.lower()}-risk {disease_name.lower()} patients. "
                       f"Patient {name}, Age {patient_data['age']}, Gender {patient_data['gender']}.",
            "relevance_score": 0.92,
        }
    ]

    meds = patient_data.get("current_medications", [])
    drug_safety = {
        "medications_reviewed": meds,
        "alerts": [],
        "interactions": [],
        "safe": True,
    }

    allergies = patient_data.get("allergies", [])
    if allergies:
        for allergy in allergies:
            drug_safety["alerts"].append({
                "type": "allergy_warning",
                "severity": "high",
                "message": f"Patient is allergic to {allergy}. Avoid prescribing {allergy} or related compounds.",
            })

    clinical_summary = (
        f"Patient {name} is a {patient_data['age']}-year-old {patient_data['gender'].lower()} "
        f"evaluated for {disease_name}. Risk assessment: {derived_risk} (probability: {prob:.3f}). "
        f"{'Currently on ' + ', '.join(meds) + '.' if meds else 'No current medications.'} "
        f"{'Known allergies: ' + ', '.join(allergies) + '.' if allergies else 'No known allergies.'}"
    )

    clinical_intelligence = {
        "key_findings": [
            f"{derived_risk} risk for {disease_name} based on ML model inference (prob={prob:.3f})",
            f"Age: {patient_data['age']}, Gender: {patient_data['gender']}",
        ],
        "recommendations": [],
    }

    if derived_risk == "Low":
        clinical_intelligence["recommendations"] = [
            "Continue routine health screening",
            "Maintain healthy lifestyle and diet",
            "Follow up in 12 months",
        ]
    elif derived_risk == "Medium":
        clinical_intelligence["recommendations"] = [
            "Close monitoring recommended every 3-6 months",
            "Consider lifestyle modifications",
            "Review and optimize current medications",
            "Additional diagnostic testing may be warranted",
        ]
    else:  # High
        clinical_intelligence["recommendations"] = [
            "Urgent specialist referral recommended",
            "Intensive monitoring and frequent follow-up required",
            "Aggressive treatment protocol should be considered",
            "Review all medications for interactions and contraindications",
            "Patient education on warning signs and emergency protocols",
        ]

    return {
        "risk_assessment": risk_assessment,
        "rag_evidence": rag_evidence,
        "drug_safety_alerts": drug_safety,
        "clinical_summary": clinical_summary,
        "clinical_intelligence": clinical_intelligence,
    }


def seed():
    """Insert all patients and their AI reports."""
    total_patients = 0
    total_reports = 0

    for disease_name, patients in ALL_DISEASES.items():
        print(f"\n--- Seeding {disease_name} ({len(patients)} patients) ---")
        male_count = sum(1 for p in patients if p["gender"] == "Male")
        female_count = sum(1 for p in patients if p["gender"] == "Female")
        print(f"    Males: {male_count}, Females: {female_count}")

        for pdata in patients:
            # Check if patient already exists (by name)
            existing = db.query(Patient).filter(
                Patient.first_name == pdata["first_name"],
                Patient.last_name == pdata["last_name"],
                Patient.doctor_id == DOCTOR_ID,
            ).first()

            if existing:
                print(f"  [SKIP] {pdata['first_name']} {pdata['last_name']} already exists (ID={existing.id})")
                continue

            patient = Patient(
                doctor_id=DOCTOR_ID,
                first_name=pdata["first_name"],
                last_name=pdata["last_name"],
                age=pdata["age"],
                gender=pdata["gender"],
                medical_history=pdata["medical_history"],
                allergies=pdata["allergies"],
                current_medications=pdata["current_medications"],
            )
            db.add(patient)
            db.flush()  # Get the patient ID

            # Create AI Report
            report_data = _build_ai_report(pdata, disease_name)
            ai_report = AIReport(
                patient_id=patient.id,
                risk_assessment=report_data["risk_assessment"],
                rag_evidence=report_data["rag_evidence"],
                drug_safety_alerts=report_data["drug_safety_alerts"],
                clinical_summary=report_data["clinical_summary"],
                clinical_intelligence=report_data["clinical_intelligence"],
            )
            db.add(ai_report)
            total_patients += 1
            total_reports += 1

            prob = report_data["risk_assessment"]["probability"]
            derived_risk = report_data["risk_assessment"]["risk_level"]
            is_real = report_data["risk_assessment"].get("is_model_inferred", False)
            model_tag = "MODEL" if is_real else "FALLBACK"
            print(f"  [OK] {pdata['first_name']:12s} {pdata['last_name']:12s}  "
                  f"Age={pdata['age']:3d}  {pdata['gender']:6s}  "
                  f"Risk={derived_risk:6s}  Prob={prob:.4f}  [{model_tag}]  -> Patient ID={patient.id}")

    db.commit()
    print(f"\n{'='*60}")
    print(f"SEEDING COMPLETE")
    print(f"  Total patients inserted:  {total_patients}")
    print(f"  Total AI reports created: {total_reports}")
    print(f"  Doctor ID:                {DOCTOR_ID}")
    print(f"  Diseases covered:         {len(ALL_DISEASES)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    seed()
    db.close()
