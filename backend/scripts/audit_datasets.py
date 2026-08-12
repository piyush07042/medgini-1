import os
import json
import hashlib
import pandas as pd
from pathlib import Path

def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def audit_dataset(csv_path: Path) -> dict:
    df = pd.read_csv(csv_path)
    rows, cols = df.shape
    # Determine target column (assume column named 'target' or last column)
    target_col = 'target' if 'target' in df.columns else df.columns[-1]
    positive = int((df[target_col] == 1).sum())
    negative = int((df[target_col] == 0).sum())
    missing = int(df.isna().sum().sum())
    duplicates = int(df.duplicated().sum())
    class_dist = df[target_col].value_counts().to_dict()
    feature_types = {col: str(df[col].dtype) for col in df.columns if col != target_col}
    sha256 = compute_sha256(csv_path)
    return {
        "dataset": csv_path.stem,
        "source": str(csv_path),
        "rows": rows,
        "features": cols - 1,
        "target": target_col,
        "positive": positive,
        "negative": negative,
        "missing_values": missing,
        "duplicates": duplicates,
        "class_distribution": class_dist,
        "feature_types": feature_types,
        "sha256": sha256,
    }

def main():
    raw_root = Path(__file__).resolve().parents[2] / "datasets" / "raw"
    audit_results = []
    for disease_dir in raw_root.iterdir():
        if disease_dir.is_dir():
            csv_path = disease_dir / "data.csv"
            if csv_path.is_file():
                audit_results.append(audit_dataset(csv_path))
    out_path = Path(__file__).resolve().parents[2] / "datasets" / "validation" / "dataset_audit.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)
    print(f"Dataset audit written to {out_path}")

if __name__ == "__main__":
    main()
