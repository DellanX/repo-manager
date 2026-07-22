import shlex
import subprocess

from src.core.config import WORKSPACE
from src.core import events


class OperationError(Exception):
    pass


def _run(cmd: list[str], cwd: str | None = None) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise OperationError(result.stderr.strip() or "Command failed")
    return result.stdout


def clone_repo(url: str) -> str:
    events.operation_events.record("service", "clone", "started", {"url": url})
    output = _run(["git", "clone", url, WORKSPACE])
    events.operation_events.record(
        "service", "clone", "completed", {"url": url})
    return output


def checkout(branch: str) -> str:
    events.operation_events.record(
        "service", "checkout", "started", {"branch": branch})
    output = _run(["git", "checkout", branch], cwd=WORKSPACE)
    events.operation_events.record(
        "service", "checkout", "completed", {"branch": branch})
    return output


def commit(message: str) -> str:
    events.operation_events.record(
        "service", "commit", "started", {"message": message})
    _run(["git", "add", "."], cwd=WORKSPACE)
    output = _run(["git", "commit", "-m", message], cwd=WORKSPACE)
    events.operation_events.record(
        "service", "commit", "completed", {"message": message})
    return output


def push(remote: str = "origin", branch: str = "main") -> str:
    events.operation_events.record("service", "push", "started", {
                                   "remote": remote, "branch": branch})
    output = _run(["git", "push", remote, branch], cwd=WORKSPACE)
    events.operation_events.record("service", "push", "completed", {
                                   "remote": remote, "branch": branch})
    return output


def exec_cmd(cmd: str) -> str:
    events.operation_events.record("service", "exec", "started", {"cmd": cmd})
    output = _run(shlex.split(cmd), cwd=WORKSPACE)
    events.operation_events.record(
        "service", "exec", "completed", {"cmd": cmd})
    return output
