from pathlib import Path
from ml.preprocessing.preprocessor import Preprocessor, PreprocessorConfig

model_dir = Path('models/heart_disease')
model_dir.mkdir(parents=True, exist_ok=True)
dataset_path = Path('datasets/processed/heart_disease/heart_disease.csv')
config = PreprocessorConfig(
    dataset_path=dataset_path,
    target_column='target',
    output_directory=model_dir,
    numeric_features=['age','trestbps','chol','thalach','oldpeak','ca'],
    categorical_features=['sex','cp','fbs','restecg','exang','slope','thal'],
)
pre = Preprocessor(config)
pre.load_dataset()
pre.validate_target()
pre.validate_features()
pre.prepare_features()
pre.build_pipeline()
pre.fit()
pre.save_pipeline()
print('created', model_dir / 'preprocessor.joblib')
print('created', model_dir / 'feature_names.json')
