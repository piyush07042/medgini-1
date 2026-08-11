import pytest


def test_scheduler_module_imports():
    # Basic import smoke test for scheduler module
    import importlib

    mod = importlib.import_module("app.core.scheduler")
    assert hasattr(mod, "start_scheduler")
    assert hasattr(mod, "shutdown_scheduler")

