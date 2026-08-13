import requests
import time
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAYLOADS = {
    "heart-disease": {"age": 50, "sex": 1, "cp": 1, "trestbps": 120, "chol": 200, "fbs": 0, "restecg": 1, "thalach": 150, "exang": 0, "oldpeak": 1.0, "slope": 2, "ca": 0, "thal": 2},
    "diabetes": {"age": 55, "time_in_hospital": 3, "num_lab_procedures": 40, "num_procedures": 1, "num_medications": 10, "number_outpatient": 0, "number_emergency": 0, "number_inpatient": 0, "number_diagnoses": 5},
    "kidney-disease": {"age": 60, "bp": 80, "sg": 1.020, "al": 0, "su": 0, "rbc": "normal", "pc": "normal", "pcc": "notpresent", "ba": "notpresent", "bgr": 100, "bu": 30, "sc": 1.0, "sod": 140, "pot": 4.5, "hemo": 15.0, "pcv": 45, "wc": 8000, "rc": 5.0, "htn": "no", "dm": "no", "cad": "no", "appet": "good", "pe": "no", "ane": "no"},
    "liver": {"age": 45, "gender": "Male", "bilirubin": 1.0, "db": 0.5, "alk_phosphatase": 150, "sgpt": 30, "sgot": 35, "tp": 7.0, "alb": 3.5, "ag_ratio": 1.0},
    "breast-cancer": {"radius_mean": 15.0, "texture_mean": 20.0, "perimeter_mean": 90.0, "area_mean": 700.0, "smoothness_mean": 0.1, "compactness_mean": 0.1, "concavity_mean": 0.1, "concave_points_mean": 0.05, "symmetry_mean": 0.2, "fractal_dimension_mean": 0.06, "radius_se": 0.5, "texture_se": 1.0, "perimeter_se": 3.0, "area_se": 50.0, "smoothness_se": 0.005, "compactness_se": 0.02, "concavity_se": 0.03, "concave_points_se": 0.01, "symmetry_se": 0.02, "fractal_dimension_se": 0.005, "radius_worst": 17.0, "texture_worst": 25.0, "perimeter_worst": 100.0, "area_worst": 900.0, "smoothness_worst": 0.15, "compactness_worst": 0.2, "concavity_worst": 0.3, "concave_points_worst": 0.1, "symmetry_worst": 0.3, "fractal_dimension_worst": 0.08},
    "parkinsons": {"MDVP_Fo": 120.0, "MDVP_Fhi": 130.0, "MDVP_Flo": 110.0, "MDVP_Jitter_perc": 0.005, "MDVP_Jitter_Abs": 0.00005, "MDVP_RAP": 0.003, "MDVP_PPQ": 0.004, "Jitter_DDP": 0.009, "MDVP_Shimmer": 0.02, "MDVP_Shimmer_dB": 0.2, "Shimmer_APQ3": 0.01, "Shimmer_APQ5": 0.015, "MDVP_APQ": 0.02, "Shimmer_DDA": 0.03, "NHR": 0.01, "HNR": 20.0, "RPDE": 0.5, "DFA": 0.7, "spread1": -5.0, "spread2": 0.2, "D2": 2.0, "PPE": 0.2},
    "hepatitis": {"age": 40, "sex": 1, "steroid": 1, "antivirals": 2, "fatigue": 1, "malaise": 2, "anorexia": 2, "liver_big": 2, "liver_firm": 2, "spleen_palpable": 2, "spiders": 2, "ascites": 2, "varices": 2, "bilirubin": 1.0, "alk_phosphatase": 80, "sgot": 30, "albumin": 4.0, "protime": 80, "histology": 1},
    "heart-failure": {"age": 60, "anaemia": 0, "creatinine_phosphokinase": 200, "diabetes": 0, "ejection_fraction": 40, "high_blood_pressure": 0, "platelets": 250000, "serum_creatinine": 1.0, "serum_sodium": 140, "sex": 1, "smoking": 0, "time": 100},
    "stroke": {"gender": "Male", "age": 65, "hypertension": 1, "heart_disease": 0, "ever_married": "Yes", "work_type": "Private", "Residence_type": "Urban", "avg_glucose_level": 100.0, "bmi": 28.0, "smoking_status": "formerly smoked"}
}

if __name__ == '__main__':
    # Start server
    proc = subprocess.Popen(["python", "-m", "uvicorn", "app.main:app", "--port", "8123"])
    
    # Wait for server to be ready
    server_ready = False
    for _ in range(60):
        try:
            response = requests.get("http://localhost:8123/api/v1/health")
            if response.status_code == 200:
                server_ready = True
                break
        except requests.exceptions.ConnectionError:
            time.sleep(2)
            
    if not server_ready:
        logger.error("Server failed to start within 120 seconds!")
        proc.kill()
        exit(1)
        
    logger.info("Server is ready, testing endpoints...")
    try:
        for endpoint, payload in PAYLOADS.items():
            url = f"http://localhost:8123/api/v1/{endpoint}/predict"
            logger.info(f"Testing {url} ...")
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"  -> SUCCESS! Disease: {data.get('disease', 'unknown')}, Prob: {data.get('probability')}")
            else:
                logger.error(f"  -> FAILED! Status: {response.status_code}, Detail: {response.text}")
    finally:
        proc.kill()
