import os
import sys
import pytest
root = os.path.dirname(os.path.abspath(__file__)) + '\\..'
root = os.path.abspath(root)
os.chdir(root)
ret = pytest.main(["--junitxml=pytest_report.xml"])
print('PYTEST_RET=', ret)
sys.exit(ret)
