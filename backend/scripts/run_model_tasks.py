"""Helper CLI to run training, evaluation, and explainability tasks.

This script is a thin wrapper that invokes existing `ml` package CLIs when
available. It supports dry-run (prints commands) and safe execution.

Usage examples:
  python scripts/run_model_tasks.py train --model heart_disease
  python scripts/run_model_tasks.py evaluate --model heart_disease --data datasets/processed/heart_disease/test.csv
  python scripts/run_model_tasks.py explain --model heart_disease --input '{"age":45,...}'
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

from ml.registry import resolve_model_directory

ROOT = Path(__file__).resolve().parents[1]


def run_command(cmd: str, dry: bool = False) -> int:
    print("Running:", cmd)
    if dry:
        return 0
    return subprocess.call(cmd, shell=True)


def train_model(model: str, dry: bool = False) -> int:
    # Attempt to call the training CLI shipped in ml.training
    cmd = f"{sys.executable} -m ml.training.trainer --model {shlex.quote(model)}"
    return run_command(cmd, dry=dry)


def evaluate_model(model: str, data: str | None = None, dry: bool = False) -> int:
    cmd = f"{sys.executable} -m ml.training.evaluator --model {shlex.quote(model)}"
    if data:
        cmd += f" --data {shlex.quote(data)}"
    return run_command(cmd, dry=dry)


def explain_prediction(model: str, input_json: str, dry: bool = False) -> int:
    # This will attempt to import the Predictor and compute SHAP if available.
    try:
        from ml.inference.predictor import load_predictor
        from ml.inference.predictor import PredictorConfig
    except Exception:
        print("ml.inference.predictor not importable; please run from repo root where ml package is available.")
        return 2

    model_dir = resolve_model_directory(model)
    if not model_dir.exists():
        print("Model directory not found:", model_dir)
        return 2

    # Load predictor and run a single prediction then attempt SHAP if available
    try:
        predictor = load_predictor(model_dir)
    except Exception as exc:
        print("Failed to load predictor:", exc)
        return 2

    try:
        inp = json.loads(input_json)
    except Exception as exc:
        print("Invalid input JSON:", exc)
        return 2

    print("Predicting with model", model)
    try:
        result = predictor.predict_json(inp)
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print("Prediction failed:", exc)
        return 2

    # Try SHAP explainability via shap.Explainer; best-effort only
    try:
        import shap
        import pandas as pd

        df = pd.DataFrame([inp])
        feature_names = getattr(predictor, "feature_names", None) or list(df.columns)
        try:
            df = df[feature_names]
        except Exception:
            pass

        def _model_fn(x):
            try:
                transformed = predictor.pipeline.transform(x)
            except Exception:
                transformed = x.values
            probs = predictor.model.predict_proba(transformed)
            return probs[:, 1]

        explainer = shap.Explainer(_model_fn, shap.maskers.Independent(df))
        sv = explainer(df)
        vals = sv.values
        if hasattr(vals, "ndim") and vals.ndim == 3:
            vals = vals[0, -1, :]
        else:
            vals = vals[0]

        pairs = sorted(zip(list(df.columns), list(map(float, vals))), key=lambda x: abs(x[1]), reverse=True)
        print("Top explainability factors:")
        for name, val in pairs[:5]:
            print(f" - {name}: {val}")

    except Exception as exc:
        print("SHAP explanation not available or failed:", exc)

    return 0


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")

    p_train = sub.add_parser("train")
    p_train.add_argument("--model", required=True)
    p_train.add_argument("--dry", action="store_true")

    p_eval = sub.add_parser("evaluate")
    p_eval.add_argument("--model", required=True)
    p_eval.add_argument("--data")
    p_eval.add_argument("--dry", action="store_true")

    p_ex = sub.add_parser("explain")
    p_ex.add_argument("--model", required=True)
    p_ex.add_argument("--input", required=True)
    p_ex.add_argument("--dry", action="store_true")

    args = parser.parse_args()

    if args.cmd == "train":
        raise SystemExit(train_model(args.model, dry=args.dry))
    if args.cmd == "evaluate":
        raise SystemExit(evaluate_model(args.model, data=args.data, dry=args.dry))
    if args.cmd == "explain":
        raise SystemExit(explain_prediction(args.model, args.input, dry=args.dry))

    parser.print_help()


if __name__ == "__main__":
    main()
