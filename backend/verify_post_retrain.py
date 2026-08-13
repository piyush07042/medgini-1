import json
import logging
from pathlib import Path
import joblib
import __main__
import numpy as np

def _to_array(x):
    if hasattr(x, "to_numpy"):
        return x.to_numpy(dtype=float)
    return np.array(x, dtype=float)

setattr(__main__, '_to_array', _to_array)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_metrics():
    master_json_path = Path("ml/evaluation/results/master_metrics.json")
    if not master_json_path.exists():
        logger.error(f"Cannot find {master_json_path}")
        return
        
    with open(master_json_path, "r") as f:
        data = json.load(f)
        
    for m in data:
        cm = m["confusion_matrix"]
        tn, fp, fn, tp = cm["TN"], cm["FP"], cm["FN"], cm["TP"]
        
        derived_acc = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        derived_prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        derived_rec = tp / (tp + fn) if (tp + fn) > 0 else 0
        
        rep_acc = m["accuracy"]
        rep_prec = m["precision"]
        rep_rec = m["recall"]
        
        logger.info(f"[{m['model_name']}]")
        logger.info(f"  Acc:  derived={derived_acc:.4f} vs reported={rep_acc:.4f}")
        logger.info(f"  Prec: derived={derived_prec:.4f} vs reported={rep_prec:.4f}")
        logger.info(f"  Rec:  derived={derived_rec:.4f} vs reported={rep_rec:.4f}")
        
        if abs(derived_acc - rep_acc) > 0.001 or abs(derived_prec - rep_prec) > 0.001 or abs(derived_rec - rep_rec) > 0.001:
            logger.warning(f"  MISMATCH found in {m['model_name']}!")

def check_models_load():
    models_dir = Path("models")
    diseases = ["heart_disease", "diabetes_model", "kidney_disease_model", "liver_disease_model", 
                "breast_cancer_model", "parkinsons_model", "hepatitis_model", "heart_failure_model", "stroke_model"]
                
    for d in diseases:
        d_dir = models_dir / d
        model_path = d_dir / "model.joblib"
        prep_path = d_dir / "preprocessor.joblib"
        feat_path = d_dir / "feature_names.json"
        
        if not model_path.exists() or not prep_path.exists() or not feat_path.exists():
            logger.error(f"[{d}] Missing files!")
            continue
            
        try:
            model = joblib.load(model_path)
            prep = joblib.load(prep_path)
            with open(feat_path, "r") as f:
                feats = json.load(f)
            logger.info(f"[{d}] Loaded model, preprocessor, and {len(feats)} features successfully.")
        except Exception as e:
            logger.error(f"[{d}] Error loading: {e}")

if __name__ == '__main__':
    check_metrics()
    check_models_load()
