import os
import sys
import pytest

root = os.path.dirname(os.path.abspath(__file__)) + '\\..'
root = os.path.abspath(root)
os.chdir(root)

# Run full test suite
sys.exit(pytest.main(['-q']))
