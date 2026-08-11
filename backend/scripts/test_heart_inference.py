from pathlib import Path
import json

from ml.inference.predictor import load_predictor
import pandas as pd

MODEL_DIR = Path('models/heart_disease')
TEST_CSV = Path('datasets/processed/heart_disease/test.csv')

print('Loading predictor from', MODEL_DIR)
predictor = load_predictor(MODEL_DIR)

if not TEST_CSV.exists():
    print('Test CSV not found at', TEST_CSV)
    raise SystemExit(1)

df = pd.read_csv(TEST_CSV)
print('Test rows:', len(df))
row = df.iloc[0].to_dict()
print('Input row sample:', {k: row[k] for k in list(row)[:10]})

result = predictor.predict_json(row)
print('Prediction result:')
print(json.dumps(result, indent=2))
