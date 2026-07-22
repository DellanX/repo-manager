from __future__ import annotations

import importlib
import os


def test_t_config_default_workspace_value(monkeypatch) -> None:
    """T-CONFIG-DEFAULT-WORKSPACE"""
    monkeypatch.delenv("REPO_MANAGER_WORKSPACE", raising=False)

    module = importlib.import_module("src.core.config")
    module = importlib.reload(module)

    assert os.getcwd() == module.WORKSPACE


def test_t_config_env_override_workspace(monkeypatch) -> None:
    """T-CONFIG-ENV-OVERRIDE"""
    monkeypatch.setenv("REPO_MANAGER_WORKSPACE", "/tmp/custom")

    module = importlib.import_module("src.core.config")
    module = importlib.reload(module)

    assert module.WORKSPACE == "/tmp/custom"
