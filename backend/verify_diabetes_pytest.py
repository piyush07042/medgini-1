import os
import pytest

os.chdir(r'd:/medigenie/backend')
rc = pytest.main(['tests/test_integration_diabetes.py', '-vv', '--disable-warnings'])
print('RC:', rc)
