from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from app.services.heart_disease_service import get_heart_disease_service
from app.schemas.heart_disease import REQUEST_EXAMPLE

svc = get_heart_disease_service(Path('models/heart_disease'))
print('initialized', svc._initialized)
print('model_directory', svc.model_directory)
print('predictor type', type(svc.predictor).__name__)
print('model type', type(svc.predictor.model).__name__)
print('model feature_names_in_', getattr(svc.predictor.model, 'feature_names_in_', None))
print('pipeline type', type(svc.predictor.pipeline).__name__)
print('pipeline repr', repr(svc.predictor.pipeline))
print('schema required columns', svc.predictor.schema.get('required_columns'))
print('schema target', svc.predictor.schema.get('target_column'))
print('schema columns', svc.predictor.schema.get('columns'))
try:
    print('pipeline steps', getattr(svc.predictor.pipeline, 'steps', None))
except Exception as exc:
    print('pipeline steps exception', exc)
try:
    df = svc.predictor.create_dataframe(REQUEST_EXAMPLE.copy())
    print('df columns', list(df.columns))
    print(df)
except Exception as exc:
    print('create_dataframe exception', exc)
