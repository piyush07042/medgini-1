"""
Seed realistic patient data for all 9 MediGenie diseases.
Each disease gets 10 patients (5 male, 5 female) with Low / Medium / High risk profiles.
All clinical values are based on real medical reference ranges and published datasets:
  - Cleveland Heart Disease Dataset (UCI)
  - Pima Indians Diabetes Dataset
  - Indian Liver Patient Dataset (ILPD)
  - UCI Chronic Kidney Disease Dataset
  - Wisconsin Breast Cancer Dataset (WBCD)
  - Oxford Parkinson's Telemonitoring Dataset
  - UCI Hepatitis Dataset
  - Heart Failure Clinical Records (Chicco & Jurman 2020)
  - Stroke Prediction Dataset (Kaggle)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.db.session import SessionLocal, create_database
from app.models.models import Patient, AIReport, User

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
#  DIABETES  (Pima-style features)
#  Fields: age, bmi, glucose, systolic_bp, insulin
# ========================================================================
DIABETES_PATIENTS = [
    # --- LOW RISK ---
    {
        "first_name": "Amit",     "last_name": "Singh",    "age": 30, "gender": "Male",
        "medical_history": {"disease": "diabetes", "risk": "Low",
            "data": {"age": 30, "bmi": 22.1, "glucose": 85, "systolic_bp": 118, "insulin": 45}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Divya",    "last_name": "Joshi",    "age": 26, "gender": "Female",
        "medical_history": {"disease": "diabetes", "risk": "Low",
            "data": {"age": 26, "bmi": 21.5, "glucose": 78, "systolic_bp": 110, "insulin": 38}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Ravi",     "last_name": "Gupta",    "age": 34, "gender": "Male",
        "medical_history": {"disease": "diabetes", "risk": "Low",
            "data": {"age": 34, "bmi": 23.8, "glucose": 92, "systolic_bp": 122, "insulin": 52}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Anita",    "last_name": "Kulkarni", "age": 45, "gender": "Female",
        "medical_history": {"disease": "diabetes", "risk": "Medium",
            "data": {"age": 45, "bmi": 28.5, "glucose": 130, "systolic_bp": 138, "insulin": 120}},
        "allergies": [], "current_medications": ["Metformin 500mg"],
    },
    {
        "first_name": "Manoj",    "last_name": "Tiwari",   "age": 50, "gender": "Male",
        "medical_history": {"disease": "diabetes", "risk": "Medium",
            "data": {"age": 50, "bmi": 29.2, "glucose": 145, "systolic_bp": 142, "insulin": 140}},
        "allergies": [], "current_medications": ["Glimepiride 2mg"],
    },
    {
        "first_name": "Sunita",   "last_name": "Desai",    "age": 48, "gender": "Female",
        "medical_history": {"disease": "diabetes", "risk": "Medium",
            "data": {"age": 48, "bmi": 27.8, "glucose": 135, "systolic_bp": 136, "insulin": 110}},
        "allergies": ["Metformin"], "current_medications": ["Sitagliptin 100mg"],
    },
    {
        "first_name": "Deepak",   "last_name": "Yadav",    "age": 53, "gender": "Male",
        "medical_history": {"disease": "diabetes", "risk": "Medium",
            "data": {"age": 53, "bmi": 30.1, "glucose": 148, "systolic_bp": 145, "insulin": 155}},
        "allergies": [], "current_medications": ["Metformin 1000mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Rekha",    "last_name": "Pandey",   "age": 62, "gender": "Female",
        "medical_history": {"disease": "diabetes", "risk": "High",
            "data": {"age": 62, "bmi": 38.5, "glucose": 220, "systolic_bp": 168, "insulin": 350}},
        "allergies": [], "current_medications": ["Insulin Glargine 30U", "Metformin 2000mg", "Atorvastatin 20mg"],
    },
    {
        "first_name": "Gopal",    "last_name": "Mishra",   "age": 65, "gender": "Male",
        "medical_history": {"disease": "diabetes", "risk": "High",
            "data": {"age": 65, "bmi": 36.2, "glucose": 245, "systolic_bp": 175, "insulin": 420}},
        "allergies": ["Sulfonamides"], "current_medications": ["Insulin Lispro", "Empagliflozin 25mg"],
    },
    {
        "first_name": "Padma",    "last_name": "Rao",      "age": 58, "gender": "Female",
        "medical_history": {"disease": "diabetes", "risk": "High",
            "data": {"age": 58, "bmi": 35.0, "glucose": 210, "systolic_bp": 162, "insulin": 310}},
        "allergies": [], "current_medications": ["Insulin Aspart", "Dapagliflozin 10mg", "Lisinopril 20mg"],
    },
]


# ========================================================================
#  KIDNEY DISEASE  (UCI CKD dataset features)
#  Fields: age, creatinine, blood_urea, sgpt, albumin
# ========================================================================
KIDNEY_DISEASE_PATIENTS = [
    # --- LOW RISK ---
    {
        "first_name": "Nikhil",   "last_name": "Bhat",     "age": 33, "gender": "Male",
        "medical_history": {"disease": "kidney_disease", "risk": "Low",
            "data": {"age": 33, "creatinine": 0.9, "blood_urea": 18, "sgpt": 22, "albumin": 4.5}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Pooja",    "last_name": "Hegde",    "age": 29, "gender": "Female",
        "medical_history": {"disease": "kidney_disease", "risk": "Low",
            "data": {"age": 29, "creatinine": 0.7, "blood_urea": 15, "sgpt": 18, "albumin": 4.8}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Arun",     "last_name": "Pillai",   "age": 36, "gender": "Male",
        "medical_history": {"disease": "kidney_disease", "risk": "Low",
            "data": {"age": 36, "creatinine": 1.0, "blood_urea": 22, "sgpt": 25, "albumin": 4.3}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Swati",    "last_name": "Patil",    "age": 50, "gender": "Female",
        "medical_history": {"disease": "kidney_disease", "risk": "Medium",
            "data": {"age": 50, "creatinine": 1.8, "blood_urea": 55, "sgpt": 48, "albumin": 3.5}},
        "allergies": [], "current_medications": ["Telmisartan 40mg"],
    },
    {
        "first_name": "Rajesh",   "last_name": "Saxena",   "age": 55, "gender": "Male",
        "medical_history": {"disease": "kidney_disease", "risk": "Medium",
            "data": {"age": 55, "creatinine": 2.1, "blood_urea": 62, "sgpt": 52, "albumin": 3.2}},
        "allergies": [], "current_medications": ["Losartan 50mg", "Furosemide 20mg"],
    },
    {
        "first_name": "Geeta",    "last_name": "Shetty",   "age": 47, "gender": "Female",
        "medical_history": {"disease": "kidney_disease", "risk": "Medium",
            "data": {"age": 47, "creatinine": 1.6, "blood_urea": 48, "sgpt": 42, "albumin": 3.6}},
        "allergies": ["NSAIDs"], "current_medications": ["Amlodipine 5mg"],
    },
    {
        "first_name": "Venkat",   "last_name": "Reddy",    "age": 52, "gender": "Male",
        "medical_history": {"disease": "kidney_disease", "risk": "Medium",
            "data": {"age": 52, "creatinine": 1.9, "blood_urea": 58, "sgpt": 45, "albumin": 3.4}},
        "allergies": [], "current_medications": ["Enalapril 10mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Kamla",    "last_name": "Devi",     "age": 68, "gender": "Female",
        "medical_history": {"disease": "kidney_disease", "risk": "High",
            "data": {"age": 68, "creatinine": 5.8, "blood_urea": 145, "sgpt": 88, "albumin": 2.1}},
        "allergies": ["Contrast dye"], "current_medications": ["Erythropoietin", "Calcium Carbonate", "Calcitriol"],
    },
    {
        "first_name": "Harish",   "last_name": "Chandra",  "age": 72, "gender": "Male",
        "medical_history": {"disease": "kidney_disease", "risk": "High",
            "data": {"age": 72, "creatinine": 7.2, "blood_urea": 168, "sgpt": 95, "albumin": 1.8}},
        "allergies": [], "current_medications": ["Sevelamer", "Iron Sucrose IV", "Epoetin alfa"],
    },
    {
        "first_name": "Savitri",  "last_name": "Prasad",   "age": 65, "gender": "Female",
        "medical_history": {"disease": "kidney_disease", "risk": "High",
            "data": {"age": 65, "creatinine": 6.5, "blood_urea": 155, "sgpt": 82, "albumin": 2.0}},
        "allergies": ["ACE inhibitors"], "current_medications": ["Dialysis 3x/week", "Cinacalcet 30mg"],
    },
]


# ========================================================================
#  LIVER DISEASE  (Indian Liver Patient Dataset features)
#  Fields: age, bilirubin, alk_phosphatase, sgpt, sgot
# ========================================================================
LIVER_DISEASE_PATIENTS = [
    # --- LOW RISK ---
    {
        "first_name": "Karthik",  "last_name": "Subramani","age": 31, "gender": "Male",
        "medical_history": {"disease": "liver_disease", "risk": "Low",
            "data": {"age": 31, "bilirubin": 0.6, "alk_phosphatase": 72, "sgpt": 18, "sgot": 22}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Neha",     "last_name": "Kapoor",   "age": 27, "gender": "Female",
        "medical_history": {"disease": "liver_disease", "risk": "Low",
            "data": {"age": 27, "bilirubin": 0.4, "alk_phosphatase": 65, "sgpt": 15, "sgot": 19}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Sanjay",   "last_name": "Malhotra", "age": 38, "gender": "Male",
        "medical_history": {"disease": "liver_disease", "risk": "Low",
            "data": {"age": 38, "bilirubin": 0.8, "alk_phosphatase": 85, "sgpt": 24, "sgot": 28}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Ritu",     "last_name": "Chauhan",  "age": 45, "gender": "Female",
        "medical_history": {"disease": "liver_disease", "risk": "Medium",
            "data": {"age": 45, "bilirubin": 2.8, "alk_phosphatase": 185, "sgpt": 68, "sgot": 75}},
        "allergies": [], "current_medications": ["Ursodeoxycholic Acid 300mg"],
    },
    {
        "first_name": "Ajay",     "last_name": "Thakur",   "age": 52, "gender": "Male",
        "medical_history": {"disease": "liver_disease", "risk": "Medium",
            "data": {"age": 52, "bilirubin": 3.2, "alk_phosphatase": 210, "sgpt": 82, "sgot": 88}},
        "allergies": [], "current_medications": ["Silymarin 140mg"],
    },
    {
        "first_name": "Manju",    "last_name": "Agarwal",  "age": 49, "gender": "Female",
        "medical_history": {"disease": "liver_disease", "risk": "Medium",
            "data": {"age": 49, "bilirubin": 2.5, "alk_phosphatase": 175, "sgpt": 62, "sgot": 70}},
        "allergies": ["Acetaminophen"], "current_medications": ["Lactulose"],
    },
    {
        "first_name": "Prakash",  "last_name": "Jha",      "age": 54, "gender": "Male",
        "medical_history": {"disease": "liver_disease", "risk": "Medium",
            "data": {"age": 54, "bilirubin": 3.5, "alk_phosphatase": 220, "sgpt": 78, "sgot": 85}},
        "allergies": [], "current_medications": ["Propranolol 40mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Saroj",    "last_name": "Kumari",   "age": 60, "gender": "Female",
        "medical_history": {"disease": "liver_disease", "risk": "High",
            "data": {"age": 60, "bilirubin": 12.5, "alk_phosphatase": 520, "sgpt": 285, "sgot": 310}},
        "allergies": ["Statins"], "current_medications": ["Rifaximin 550mg", "Lactulose", "Spironolactone 100mg"],
    },
    {
        "first_name": "Bharat",   "last_name": "Saxena",   "age": 58, "gender": "Male",
        "medical_history": {"disease": "liver_disease", "risk": "High",
            "data": {"age": 58, "bilirubin": 15.0, "alk_phosphatase": 580, "sgpt": 320, "sgot": 350}},
        "allergies": [], "current_medications": ["Albumin infusion", "Furosemide 80mg", "Vitamin K"],
    },
    {
        "first_name": "Usha",     "last_name": "Tripathi", "age": 63, "gender": "Female",
        "medical_history": {"disease": "liver_disease", "risk": "High",
            "data": {"age": 63, "bilirubin": 10.8, "alk_phosphatase": 480, "sgpt": 260, "sgot": 290}},
        "allergies": ["NSAIDs"], "current_medications": ["Terlipressin", "Octreotide", "Albumin IV"],
    },
]


# ========================================================================
#  BREAST CANCER  (Wisconsin WBCD features)
#  Fields: radius_mean, texture_mean, perimeter_mean, area_mean, smoothness_mean
# ========================================================================
BREAST_CANCER_PATIENTS = [
    # --- LOW RISK (Benign profiles) ---
    {
        "first_name": "Nandini",  "last_name": "Sen",      "age": 34, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "Low",
            "data": {"radius_mean": 10.2, "texture_mean": 15.8, "perimeter_mean": 65.0, "area_mean": 320.0, "smoothness_mean": 0.078}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Manish",   "last_name": "Dubey",    "age": 40, "gender": "Male",
        "medical_history": {"disease": "breast_cancer", "risk": "Low",
            "data": {"radius_mean": 11.5, "texture_mean": 16.2, "perimeter_mean": 72.5, "area_mean": 410.0, "smoothness_mean": 0.082}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Suman",    "last_name": "Ghosh",    "age": 38, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "Low",
            "data": {"radius_mean": 9.8, "texture_mean": 14.5, "perimeter_mean": 62.0, "area_mean": 295.0, "smoothness_mean": 0.075}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Alok",     "last_name": "Srivastava","age": 52, "gender": "Male",
        "medical_history": {"disease": "breast_cancer", "risk": "Medium",
            "data": {"radius_mean": 14.2, "texture_mean": 19.5, "perimeter_mean": 92.0, "area_mean": 620.0, "smoothness_mean": 0.098}},
        "allergies": [], "current_medications": ["Tamoxifen 20mg"],
    },
    {
        "first_name": "Rina",     "last_name": "Mukherjee","age": 48, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "Medium",
            "data": {"radius_mean": 15.0, "texture_mean": 20.8, "perimeter_mean": 97.0, "area_mean": 700.0, "smoothness_mean": 0.102}},
        "allergies": [], "current_medications": ["Letrozole 2.5mg"],
    },
    {
        "first_name": "Vinod",    "last_name": "Khanna",   "age": 55, "gender": "Male",
        "medical_history": {"disease": "breast_cancer", "risk": "Medium",
            "data": {"radius_mean": 13.8, "texture_mean": 18.9, "perimeter_mean": 89.5, "area_mean": 585.0, "smoothness_mean": 0.095}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Archana",  "last_name": "Rao",      "age": 50, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "Medium",
            "data": {"radius_mean": 14.8, "texture_mean": 21.0, "perimeter_mean": 95.0, "area_mean": 680.0, "smoothness_mean": 0.100}},
        "allergies": [], "current_medications": ["Anastrozole 1mg"],
    },
    # --- HIGH RISK (Malignant profiles) ---
    {
        "first_name": "Chitra",   "last_name": "Banerjee", "age": 62, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "High",
            "data": {"radius_mean": 21.5, "texture_mean": 28.5, "perimeter_mean": 142.0, "area_mean": 1420.0, "smoothness_mean": 0.135}},
        "allergies": ["Doxorubicin"], "current_medications": ["Trastuzumab", "Pertuzumab", "Paclitaxel"],
    },
    {
        "first_name": "Satish",   "last_name": "Agrawal",  "age": 58, "gender": "Male",
        "medical_history": {"disease": "breast_cancer", "risk": "High",
            "data": {"radius_mean": 20.2, "texture_mean": 26.8, "perimeter_mean": 135.0, "area_mean": 1280.0, "smoothness_mean": 0.128}},
        "allergies": [], "current_medications": ["Cyclophosphamide", "5-Fluorouracil"],
    },
    {
        "first_name": "Jaya",     "last_name": "Sharma",   "age": 65, "gender": "Female",
        "medical_history": {"disease": "breast_cancer", "risk": "High",
            "data": {"radius_mean": 23.0, "texture_mean": 30.2, "perimeter_mean": 150.0, "area_mean": 1600.0, "smoothness_mean": 0.142}},
        "allergies": [], "current_medications": ["Carboplatin", "Docetaxel", "Tamoxifen 20mg"],
    },
]


# ========================================================================
#  PARKINSON'S  (Oxford Telemonitoring Dataset)
#  Fields: age, motor_UPDRS, total_UPDRS, Jitter_local, Shimmer_local
# ========================================================================
PARKINSONS_PATIENTS = [
    # --- LOW RISK ---
    {
        "first_name": "Dhruv",    "last_name": "Kapoor",   "age": 42, "gender": "Male",
        "medical_history": {"disease": "parkinsons", "risk": "Low",
            "data": {"age": 42, "motor_UPDRS": 5.2, "total_UPDRS": 8.5, "Jitter_local": 0.002, "Shimmer_local": 0.012}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Shweta",   "last_name": "Verma",    "age": 38, "gender": "Female",
        "medical_history": {"disease": "parkinsons", "risk": "Low",
            "data": {"age": 38, "motor_UPDRS": 4.8, "total_UPDRS": 7.2, "Jitter_local": 0.0018, "Shimmer_local": 0.010}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Gaurav",   "last_name": "Saxena",   "age": 45, "gender": "Male",
        "medical_history": {"disease": "parkinsons", "risk": "Low",
            "data": {"age": 45, "motor_UPDRS": 6.0, "total_UPDRS": 10.0, "Jitter_local": 0.0025, "Shimmer_local": 0.014}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Shalini",  "last_name": "Tiwari",   "age": 58, "gender": "Female",
        "medical_history": {"disease": "parkinsons", "risk": "Medium",
            "data": {"age": 58, "motor_UPDRS": 22.5, "total_UPDRS": 32.0, "Jitter_local": 0.008, "Shimmer_local": 0.045}},
        "allergies": [], "current_medications": ["Levodopa/Carbidopa 25/100mg"],
    },
    {
        "first_name": "Mohan",    "last_name": "Das",      "age": 62, "gender": "Male",
        "medical_history": {"disease": "parkinsons", "risk": "Medium",
            "data": {"age": 62, "motor_UPDRS": 25.0, "total_UPDRS": 38.0, "Jitter_local": 0.010, "Shimmer_local": 0.055}},
        "allergies": [], "current_medications": ["Pramipexole 0.5mg", "Levodopa/Carbidopa"],
    },
    {
        "first_name": "Kiran",    "last_name": "Bose",     "age": 55, "gender": "Female",
        "medical_history": {"disease": "parkinsons", "risk": "Medium",
            "data": {"age": 55, "motor_UPDRS": 20.0, "total_UPDRS": 30.0, "Jitter_local": 0.007, "Shimmer_local": 0.040}},
        "allergies": [], "current_medications": ["Rasagiline 1mg"],
    },
    {
        "first_name": "Prasad",   "last_name": "Menon",    "age": 60, "gender": "Male",
        "medical_history": {"disease": "parkinsons", "risk": "Medium",
            "data": {"age": 60, "motor_UPDRS": 24.0, "total_UPDRS": 36.0, "Jitter_local": 0.009, "Shimmer_local": 0.050}},
        "allergies": [], "current_medications": ["Ropinirole 4mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Prema",    "last_name": "Naidu",    "age": 72, "gender": "Female",
        "medical_history": {"disease": "parkinsons", "risk": "High",
            "data": {"age": 72, "motor_UPDRS": 42.0, "total_UPDRS": 65.0, "Jitter_local": 0.025, "Shimmer_local": 0.095}},
        "allergies": ["Anticholinergics"], "current_medications": ["Levodopa/Carbidopa/Entacapone", "Amantadine 100mg"],
    },
    {
        "first_name": "Shankar",  "last_name": "Pillai",   "age": 75, "gender": "Male",
        "medical_history": {"disease": "parkinsons", "risk": "High",
            "data": {"age": 75, "motor_UPDRS": 48.0, "total_UPDRS": 72.0, "Jitter_local": 0.030, "Shimmer_local": 0.10}},
        "allergies": [], "current_medications": ["Deep Brain Stimulation", "Levodopa 600mg/day", "Clonazepam 0.5mg"],
    },
    {
        "first_name": "Vimala",   "last_name": "Krishnan", "age": 70, "gender": "Female",
        "medical_history": {"disease": "parkinsons", "risk": "High",
            "data": {"age": 70, "motor_UPDRS": 45.0, "total_UPDRS": 68.0, "Jitter_local": 0.028, "Shimmer_local": 0.098}},
        "allergies": [], "current_medications": ["Apomorphine pump", "Levodopa CR 500mg"],
    },
]


# ========================================================================
#  HEPATITIS  (UCI Hepatitis Dataset features)
#  Fields: age, bilirubin, alk_phosphatase, sgpt, sgot
# ========================================================================
HEPATITIS_PATIENTS = [
    # --- LOW RISK ---
    {
        "first_name": "Rohit",    "last_name": "Sinha",    "age": 29, "gender": "Male",
        "medical_history": {"disease": "hepatitis", "risk": "Low",
            "data": {"age": 29, "bilirubin": 0.5, "alk_phosphatase": 62, "sgpt": 16, "sgot": 20}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Tanvi",    "last_name": "Shah",     "age": 25, "gender": "Female",
        "medical_history": {"disease": "hepatitis", "risk": "Low",
            "data": {"age": 25, "bilirubin": 0.4, "alk_phosphatase": 55, "sgpt": 14, "sgot": 18}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Vishal",   "last_name": "Awasthi",  "age": 34, "gender": "Male",
        "medical_history": {"disease": "hepatitis", "risk": "Low",
            "data": {"age": 34, "bilirubin": 0.7, "alk_phosphatase": 70, "sgpt": 20, "sgot": 24}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Pallavi",  "last_name": "Garg",     "age": 42, "gender": "Female",
        "medical_history": {"disease": "hepatitis", "risk": "Medium",
            "data": {"age": 42, "bilirubin": 2.2, "alk_phosphatase": 145, "sgpt": 65, "sgot": 72}},
        "allergies": [], "current_medications": ["Entecavir 0.5mg"],
    },
    {
        "first_name": "Ashok",    "last_name": "Bansal",   "age": 48, "gender": "Male",
        "medical_history": {"disease": "hepatitis", "risk": "Medium",
            "data": {"age": 48, "bilirubin": 2.8, "alk_phosphatase": 160, "sgpt": 78, "sgot": 82}},
        "allergies": [], "current_medications": ["Tenofovir 300mg"],
    },
    {
        "first_name": "Sushma",   "last_name": "Malhotra", "age": 44, "gender": "Female",
        "medical_history": {"disease": "hepatitis", "risk": "Medium",
            "data": {"age": 44, "bilirubin": 2.0, "alk_phosphatase": 135, "sgpt": 58, "sgot": 65}},
        "allergies": [], "current_medications": ["Sofosbuvir/Velpatasvir"],
    },
    {
        "first_name": "Girish",   "last_name": "Wadia",    "age": 50, "gender": "Male",
        "medical_history": {"disease": "hepatitis", "risk": "Medium",
            "data": {"age": 50, "bilirubin": 3.0, "alk_phosphatase": 170, "sgpt": 72, "sgot": 78}},
        "allergies": ["Interferon"], "current_medications": ["Ribavirin 1000mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Leela",    "last_name": "Nambiar",  "age": 58, "gender": "Female",
        "medical_history": {"disease": "hepatitis", "risk": "High",
            "data": {"age": 58, "bilirubin": 8.5, "alk_phosphatase": 420, "sgpt": 245, "sgot": 280}},
        "allergies": [], "current_medications": ["Sofosbuvir/Ledipasvir", "Ribavirin", "Lactulose"],
    },
    {
        "first_name": "Dinesh",   "last_name": "Gupta",    "age": 62, "gender": "Male",
        "medical_history": {"disease": "hepatitis", "risk": "High",
            "data": {"age": 62, "bilirubin": 10.2, "alk_phosphatase": 480, "sgpt": 290, "sgot": 320}},
        "allergies": ["Penicillin"], "current_medications": ["PEG-Interferon", "Entecavir 1mg", "Albumin IV"],
    },
    {
        "first_name": "Radha",    "last_name": "Krishna",  "age": 55, "gender": "Female",
        "medical_history": {"disease": "hepatitis", "risk": "High",
            "data": {"age": 55, "bilirubin": 9.0, "alk_phosphatase": 450, "sgpt": 265, "sgot": 295}},
        "allergies": [], "current_medications": ["Glecaprevir/Pibrentasvir", "Spironolactone 50mg"],
    },
]


# ========================================================================
#  HEART FAILURE  (Chicco & Jurman 2020 dataset features)
#  Fields: age, ejection_fraction, serum_creatinine, serum_sodium, time
# ========================================================================
HEART_FAILURE_PATIENTS = [
    # --- LOW RISK ---
    {
        "first_name": "Aarav",    "last_name": "Jain",     "age": 40, "gender": "Male",
        "medical_history": {"disease": "heart_failure", "risk": "Low",
            "data": {"age": 40, "ejection_fraction": 62, "serum_creatinine": 0.8, "serum_sodium": 140, "time": 250}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Ishita",   "last_name": "Oberoi",   "age": 35, "gender": "Female",
        "medical_history": {"disease": "heart_failure", "risk": "Low",
            "data": {"age": 35, "ejection_fraction": 65, "serum_creatinine": 0.7, "serum_sodium": 142, "time": 280}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Vivek",    "last_name": "Choudhary","age": 42, "gender": "Male",
        "medical_history": {"disease": "heart_failure", "risk": "Low",
            "data": {"age": 42, "ejection_fraction": 58, "serum_creatinine": 0.9, "serum_sodium": 139, "time": 230}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Madhuri",  "last_name": "Nene",     "age": 58, "gender": "Female",
        "medical_history": {"disease": "heart_failure", "risk": "Medium",
            "data": {"age": 58, "ejection_fraction": 35, "serum_creatinine": 1.5, "serum_sodium": 134, "time": 120}},
        "allergies": [], "current_medications": ["Enalapril 10mg", "Carvedilol 12.5mg"],
    },
    {
        "first_name": "Pankaj",   "last_name": "Tripathi", "age": 60, "gender": "Male",
        "medical_history": {"disease": "heart_failure", "risk": "Medium",
            "data": {"age": 60, "ejection_fraction": 30, "serum_creatinine": 1.8, "serum_sodium": 132, "time": 100}},
        "allergies": [], "current_medications": ["Sacubitril/Valsartan 50mg", "Spironolactone 25mg"],
    },
    {
        "first_name": "Seema",    "last_name": "Biswas",   "age": 55, "gender": "Female",
        "medical_history": {"disease": "heart_failure", "risk": "Medium",
            "data": {"age": 55, "ejection_fraction": 38, "serum_creatinine": 1.3, "serum_sodium": 135, "time": 140}},
        "allergies": [], "current_medications": ["Bisoprolol 5mg", "Furosemide 40mg"],
    },
    {
        "first_name": "Rajendra", "last_name": "Prasad",   "age": 62, "gender": "Male",
        "medical_history": {"disease": "heart_failure", "risk": "Medium",
            "data": {"age": 62, "ejection_fraction": 32, "serum_creatinine": 1.6, "serum_sodium": 133, "time": 110}},
        "allergies": ["ACE inhibitors"], "current_medications": ["Valsartan 80mg", "Ivabradine 5mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Kasturi",  "last_name": "Behera",   "age": 75, "gender": "Female",
        "medical_history": {"disease": "heart_failure", "risk": "High",
            "data": {"age": 75, "ejection_fraction": 14, "serum_creatinine": 4.5, "serum_sodium": 118, "time": 15}},
        "allergies": [], "current_medications": ["Dobutamine drip", "Furosemide IV", "Milrinone"],
    },
    {
        "first_name": "Mahendra", "last_name": "Tomar",    "age": 78, "gender": "Male",
        "medical_history": {"disease": "heart_failure", "risk": "High",
            "data": {"age": 78, "ejection_fraction": 12, "serum_creatinine": 5.2, "serum_sodium": 115, "time": 10}},
        "allergies": ["Beta-blockers"], "current_medications": ["LVAD candidate", "IV Diuretics", "Digoxin 0.125mg"],
    },
    {
        "first_name": "Pushpa",   "last_name": "Devi",     "age": 72, "gender": "Female",
        "medical_history": {"disease": "heart_failure", "risk": "High",
            "data": {"age": 72, "ejection_fraction": 15, "serum_creatinine": 4.0, "serum_sodium": 120, "time": 20}},
        "allergies": [], "current_medications": ["Sacubitril/Valsartan 100mg", "Furosemide 80mg", "Metolazone 5mg"],
    },
]


# ========================================================================
#  STROKE  (Kaggle Stroke Prediction Dataset features)
#  Fields: age, hypertension, heart_disease, avg_glucose_level, bmi, smoking_status
# ========================================================================
STROKE_PATIENTS = [
    # --- LOW RISK ---
    {
        "first_name": "Kabir",    "last_name": "Mehra",    "age": 30, "gender": "Male",
        "medical_history": {"disease": "stroke", "risk": "Low",
            "data": {"age": 30, "hypertension": 0, "heart_disease": 0, "avg_glucose_level": 82.5, "bmi": 22.0, "smoking_status": "never smoked"}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Tara",     "last_name": "Menon",    "age": 28, "gender": "Female",
        "medical_history": {"disease": "stroke", "risk": "Low",
            "data": {"age": 28, "hypertension": 0, "heart_disease": 0, "avg_glucose_level": 78.0, "bmi": 21.5, "smoking_status": "never smoked"}},
        "allergies": [], "current_medications": [],
    },
    {
        "first_name": "Sameer",   "last_name": "Vohra",    "age": 35, "gender": "Male",
        "medical_history": {"disease": "stroke", "risk": "Low",
            "data": {"age": 35, "hypertension": 0, "heart_disease": 0, "avg_glucose_level": 88.0, "bmi": 24.2, "smoking_status": "never smoked"}},
        "allergies": [], "current_medications": [],
    },
    # --- MEDIUM RISK ---
    {
        "first_name": "Veena",    "last_name": "Kashyap",  "age": 55, "gender": "Female",
        "medical_history": {"disease": "stroke", "risk": "Medium",
            "data": {"age": 55, "hypertension": 1, "heart_disease": 0, "avg_glucose_level": 135.0, "bmi": 30.5, "smoking_status": "formerly smoked"}},
        "allergies": [], "current_medications": ["Amlodipine 5mg", "Aspirin 81mg"],
    },
    {
        "first_name": "Naresh",   "last_name": "Goyal",    "age": 58, "gender": "Male",
        "medical_history": {"disease": "stroke", "risk": "Medium",
            "data": {"age": 58, "hypertension": 1, "heart_disease": 0, "avg_glucose_level": 148.0, "bmi": 31.2, "smoking_status": "smokes"}},
        "allergies": [], "current_medications": ["Losartan 100mg", "Atorvastatin 20mg"],
    },
    {
        "first_name": "Rashmi",   "last_name": "Batra",    "age": 52, "gender": "Female",
        "medical_history": {"disease": "stroke", "risk": "Medium",
            "data": {"age": 52, "hypertension": 1, "heart_disease": 0, "avg_glucose_level": 128.0, "bmi": 29.0, "smoking_status": "formerly smoked"}},
        "allergies": [], "current_medications": ["Indapamide 1.5mg"],
    },
    {
        "first_name": "Hemant",   "last_name": "Khandelwal","age": 56, "gender": "Male",
        "medical_history": {"disease": "stroke", "risk": "Medium",
            "data": {"age": 56, "hypertension": 1, "heart_disease": 1, "avg_glucose_level": 155.0, "bmi": 32.0, "smoking_status": "smokes"}},
        "allergies": [], "current_medications": ["Clopidogrel 75mg", "Ramipril 5mg"],
    },
    # --- HIGH RISK ---
    {
        "first_name": "Sumitra",  "last_name": "Chauhan",  "age": 72, "gender": "Female",
        "medical_history": {"disease": "stroke", "risk": "High",
            "data": {"age": 72, "hypertension": 1, "heart_disease": 1, "avg_glucose_level": 240.0, "bmi": 38.5, "smoking_status": "formerly smoked"}},
        "allergies": ["Heparin"], "current_medications": ["Warfarin", "Metoprolol 100mg", "Insulin Glargine"],
    },
    {
        "first_name": "Jagdish",  "last_name": "Prasad",   "age": 78, "gender": "Male",
        "medical_history": {"disease": "stroke", "risk": "High",
            "data": {"age": 78, "hypertension": 1, "heart_disease": 1, "avg_glucose_level": 265.0, "bmi": 36.0, "smoking_status": "formerly smoked"}},
        "allergies": [], "current_medications": ["Apixaban 5mg", "Atorvastatin 80mg", "Amlodipine 10mg"],
    },
    {
        "first_name": "Kamini",   "last_name": "Lal",      "age": 68, "gender": "Female",
        "medical_history": {"disease": "stroke", "risk": "High",
            "data": {"age": 68, "hypertension": 1, "heart_disease": 1, "avg_glucose_level": 228.0, "bmi": 35.5, "smoking_status": "smokes"}},
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
    """Build an AIReport JSON payload from the patient seed data."""
    risk = patient_data["medical_history"]["risk"]
    data = patient_data["medical_history"]["data"]
    disease_key = patient_data["medical_history"]["disease"]
    name = f"{patient_data['first_name']} {patient_data['last_name']}"

    # Map risk to probability ranges
    risk_prob = {"Low": 0.15, "Medium": 0.55, "High": 0.88}
    prob = risk_prob.get(risk, 0.5)

    risk_assessment = {
        "disease": disease_name,
        "disease_key": disease_key,
        "risk_level": risk,
        "risk_category": risk,
        "probability": prob,
        "confidence": round(prob + 0.05, 2) if prob < 0.95 else 0.95,
        "confidence_label": f"{risk} Risk",
        "prediction": 1 if risk in ("Medium", "High") else 0,
        "input_features": data,
        "class_probabilities": {"0": round(1 - prob, 3), "1": round(prob, 3)},
    }

    rag_evidence = [
        {
            "source": f"Clinical Guidelines for {disease_name}",
            "content": f"Standard clinical protocol for {risk.lower()}-risk {disease_name.lower()} patients. "
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
        f"evaluated for {disease_name}. Risk assessment: {risk}. "
        f"{'Currently on ' + ', '.join(meds) + '.' if meds else 'No current medications.'} "
        f"{'Known allergies: ' + ', '.join(allergies) + '.' if allergies else 'No known allergies.'}"
    )

    clinical_intelligence = {
        "key_findings": [
            f"{risk} risk for {disease_name} based on clinical markers",
            f"Age: {patient_data['age']}, Gender: {patient_data['gender']}",
        ],
        "recommendations": [],
    }

    if risk == "Low":
        clinical_intelligence["recommendations"] = [
            "Continue routine health screening",
            "Maintain healthy lifestyle and diet",
            "Follow up in 12 months",
        ]
    elif risk == "Medium":
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

            risk = pdata["medical_history"]["risk"]
            print(f"  [OK] {pdata['first_name']:12s} {pdata['last_name']:12s}  "
                  f"Age={pdata['age']:3d}  {pdata['gender']:6s}  Risk={risk:6s}  -> Patient ID={patient.id}")

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
