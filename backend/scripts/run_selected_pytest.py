import os
import pytest
import io
from contextlib import redirect_stdout, redirect_stderr

paths = [
    'tests/test_integration_hepatitis.py',
    'tests/test_integration_breast_cancer.py',
    'tests/test_integration_diabetes.py',
    'tests/test_integration_cleanup.py',
]

out_path = 'pytest_selected_output.txt'
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)
with open(out_path, 'w', encoding='utf-8') as fh:
    buf = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            ret = pytest.main(['-q'] + paths)
    except SystemExit as e:
        ret = e.code
    fh.write(buf.getvalue())
    fh.write(f"\nEXIT_CODE: {ret}\n")
print('WROTE', out_path)
