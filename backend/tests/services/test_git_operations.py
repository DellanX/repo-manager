from __future__ import annotations

import subprocess
from dataclasses import dataclass

import pytest
from src.core import events
from src.services import git_operations
from src.services.git_operations import OperationError


@dataclass
class DummyCompleted:
    returncode: int
    stdout: str
    stderr: str


def test_t_git_run_success_returns_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-GIT-RUN-STDOUT"""

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        assert capture_output is True
        assert text is True
        return DummyCompleted(0, "ok", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert git_operations._run(["git", "status"]) == "ok"


def test_t_git_run_failure_uses_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-GIT-RUN-ERROR-STDERR"""

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        return DummyCompleted(1, "", "fatal")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(OperationError, match="fatal"):
        git_operations._run(["git", "status"])


def test_t_git_run_failure_fallback_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-GIT-RUN-ERROR-FALLBACK"""

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        return DummyCompleted(1, "", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(OperationError, match="Command failed"):
        git_operations._run(["git", "status"])


def test_t_git_commit_runs_add_then_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-GIT-COMMIT-SEQUENCE"""
    calls: list[list[str]] = []

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        calls.append(cmd)
        return DummyCompleted(0, "ok", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    git_operations.commit("msg")

    assert calls[0] == ["git", "add", "."]
    assert calls[1] == ["git", "commit", "-m", "msg"]


def test_t_git_clone_runs_in_workspace(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-GIT-CLONE-IN-WORKSPACE"""
    captured = {}

    def fake_run(cmd, cwd=None, capture_output=True, text=True):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return DummyCompleted(0, "ok", "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    git_operations.clone_repo("https://example/repo.git")

    assert captured["cmd"] == ["git", "clone", "https://example/repo.git"]
    assert captured["cwd"] == git_operations.WORKSPACE


@pytest.mark.parametrize(
    ("op", "args", "expected"),
    [
        (git_operations.clone_repo, ("https://example/repo.git",), "clone"),
        (git_operations.checkout, ("main",), "checkout"),
        (git_operations.push, ("origin", "main"), "push"),
        (git_operations.exec_cmd, ("git status",), "exec"),
    ],
)
def test_t_git_operations_emit_started_and_completed(
    monkeypatch: pytest.MonkeyPatch,
    op,
    args,
    expected: str,
) -> None:
    """T-GIT-EVENTS-STARTED-COMPLETED"""

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, cwd=None, capture_output=True, text=True: DummyCompleted(0, "ok", ""),
    )

    op(*args)
    items = events.operation_events.list_since(0)
    statuses = [(e.operation, e.status) for e in items]
    assert (expected, "started") in statuses
    assert (expected, "completed") in statuses


def test_t_git_run_no_shell_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-GIT-NO-SHELL-TRUE: Verify subprocess.run is not called with shell=True."""
    calls = []

    def capturing_run(cmd, **kwargs):
        calls.append({"cmd": cmd, "kwargs": kwargs})
        return DummyCompleted(0, "ok", "")

    monkeypatch.setattr(subprocess, "run", capturing_run)
    git_operations._run(["git", "status"])

    assert len(calls) == 1
    assert "shell" not in calls[0]["kwargs"] or calls[0]["kwargs"]["shell"] is False
