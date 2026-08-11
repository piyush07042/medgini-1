import sys
import io
import pytest
from contextlib import redirect_stdout, redirect_stderr

out_path = 'pytest_verbose_capture.txt'
with open(out_path, 'w', encoding='utf-8') as fh:
    buf = io.StringIO()
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            ret = pytest.main(['-vv'])
    except SystemExit as e:
        ret = e.code
    fh.write(buf.getvalue())
    fh.write(f"\nEXIT_CODE: {ret}\n")
print('WROTE', out_path)
