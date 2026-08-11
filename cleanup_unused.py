from pathlib import Path
import shutil

root = Path('E:/MediGenie-main')

# Files/directories that are likely generated/log/test outputs and not core source.
# Keep source code, configuration, and package manifests.
entries = [
    'coverage_report.txt',
    'terminal_test_output.txt',
    'read.txt',
    'MediGenie_Synopsis_Final (1).docx',
    'logs',
    'backend/coverage_run.out',
    'backend/pyout.txt',
    'backend/terminal_test_output.txt',
    'backend/tree_structure.txt',
    'backend/tmp_pipeline_run.log',
    'backend/tmp_pipeline_full.log',
    'backend/tmp_all_models.log',
    'backend/tmp_debug_heart.py',
    'backend/tmp_debug_heart2.py',
    'backend/tmp_pytest_runner.py',
    'backend/tmp_pytest_runner_capture.py',
    'backend/tmp_verify_supervisor.py',
    'backend/tmp_verify_db.py',
    'backend/tmp_verify_dashboard.py',
    'backend/tmp_route_inspect.py',
    'backend/tmp_register_test.py',
    'backend/tmp_recommendation_debug.py',
    'backend/tmp_coverage_runner.py',
    'backend/tmp_coverage_run_capture.py',
    'backend/pytest_breast_output.txt',
    'backend/pytest_all_output.txt',
    'backend/pytest_capture_output.txt',
    'backend/pytest_diabetes_out.txt',
    'backend/pytest_exit.txt',
    'backend/pytest_full_capture.txt',
    'backend/pytest_full_output.txt',
    'backend/pytest_heart_exit.txt',
    'backend/pytest_heart_results.txt',
    'backend/pytest_isolated_output.txt',
    'backend/pytest_out.txt',
    'backend/pytest_report_output.txt',
    'backend/pytest_selected_output.txt',
    'backend/pytest_stderr.txt',
    'backend/pytest_stdout.txt',
    'backend/pytest_verbose.txt',
    'backend/pytest_version.txt',
    'backend/python_test_version.txt',
    'backend/report_test_out.txt',
    'backend/report_test_out2.txt',
    'backend/temp_reports',
    'backend/temp_uploads',
    'backend/workspace',
    'backend/.coverage',
    'frontend/build-log.txt',
    'frontend/build-debug.txt',
    'frontend/build-check.log',
    'frontend/install-output.txt',
]

for entry in entries:
    target = root / entry
    if not target.exists():
        print(f'SKIP missing: {entry}')
        continue
    try:
        if target.is_dir():
            shutil.rmtree(target)
            print(f'Removed dir: {entry}')
        else:
            target.unlink()
            print(f'Removed file: {entry}')
    except Exception as exc:
        print(f'ERROR removing {entry}: {exc}')
