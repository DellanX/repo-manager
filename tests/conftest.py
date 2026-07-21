from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.core import events
from src.server import app


@pytest.fixture()
def temp_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    # Patch workspace constants where they are imported by value.
    monkeypatch.setattr("src.core.config.WORKSPACE", str(workspace))
    monkeypatch.setattr("src.services.file_operations.WORKSPACE", str(workspace))
    monkeypatch.setattr("src.services.git_operations.WORKSPACE", str(workspace))
    return workspace


@pytest.fixture(autouse=True)
def reset_event_store() -> None:
    events.operation_events = events.OperationEventStore()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
