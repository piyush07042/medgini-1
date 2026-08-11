from pathlib import Path
import pytest

paths = ["tests/agents/test_report_generation.py", "tests/test_report_templates.py", "tests/test_e2e_report_generation.py"]
result = pytest.main(["-vv", "--maxfail=1", *paths])
print("PYTEST_EXIT_CODE=", result)
