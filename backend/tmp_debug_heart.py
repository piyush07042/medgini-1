from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from app.services.heart_disease_service import get_heart_disease_service
from app.schemas.heart_disease import REQUEST_EXAMPLE

svc = get_heart_disease_service(Path('models/heart_disease'))
print('initialized', svc._initialized)
print('model_directory', svc.model_directory)
print('predictor model', type(svc.predictor.model).__name__)
try:
    out = svc.predict(REQUEST_EXAMPLE.copy())
    print('output keys', list(out.keys()))
    print(out)
except Exception as exc:
    import traceback
    print('exception', exc)
    traceback.print_exc()
