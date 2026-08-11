"""
Runner script for Model Verification & Evaluation.

Iterates over all 9 disease models, runs complete dataset & model verification,
computes metrics, cross-validation, and explainability, and saves plots.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from evaluation.evaluator import DISEASE_MODEL_MAP, DiseaseModelEvaluator


def main():
    print("=" * 70)
    print("Starting MediGenie Model Verification & Evaluation Harness")
    print("Target: 100% ML Validation across 9 Disease Models")
    print("=" * 70)

    summary_all = {}
    for disease_key in DISEASE_MODEL_MAP.keys():
        try:
            evaluator = DiseaseModelEvaluator(disease_key)
            res = evaluator.run_all()
            summary_all[disease_key] = {
                "name": res["disease_name"],
                "f1_score": res["metrics"]["f1_score"],
                "accuracy": res["metrics"]["accuracy"],
                "roc_auc": res["metrics"]["roc_auc"],
                "verified": res["model_verification"]["100_percent_ml_validation"],
            }
            print(f"[OK] Successfully evaluated {res['disease_name']} (F1: {res['metrics']['f1_score']:.4f}, AUC: {res['metrics']['roc_auc']:.4f})")
        except Exception as e:
            print(f"[FAIL] Failed evaluating {disease_key}: {e}")

            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"Completed evaluation for {len(summary_all)} / {len(DISEASE_MODEL_MAP)} models.")
    print("=" * 70)


if __name__ == "__main__":
    main()
