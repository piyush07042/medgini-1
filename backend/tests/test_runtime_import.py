from __future__ import annotations

import importlib


def test_app_module_imports() -> None:
    module = importlib.import_module("app.main")
    assert hasattr(module, "app")


def test_repo_root_main_module_imports() -> None:
    module = importlib.import_module("main")
    assert hasattr(module, "app")
