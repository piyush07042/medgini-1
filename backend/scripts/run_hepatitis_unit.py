from app.services.hepatitis_service import get_hepatitis_service
from app.schemas.hepatitis import REQUEST_EXAMPLE

service = get_hepatitis_service('models/hepatitis_model')
print('Service model_directory=', service.model_directory)
res = service.predict(REQUEST_EXAMPLE)
print('RESULT=', res)
