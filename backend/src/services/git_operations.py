import shlex
import subprocess
import os
from pathlib import Path

from src.core import events
from src.core.config import WORKSPACE


class OperationError(Exception):
    pass


def _resolve_clone_destination(destination: str | None) -> str | None:
    if not destination:
        return None

    workspace_root = os.path.abspath(WORKSPACE)
    raw_target = destination.strip()
    if not raw_target:
        raise OperationError("Destination cannot be empty")

    candidate = (
        os.path.abspath(raw_target)
        if os.path.isabs(raw_target)
        else os.path.abspath(os.path.join(workspace_root, raw_target))
    )

    if candidate != workspace_root and not candidate.startswith(workspace_root + os.sep):
        raise OperationError("Destination escapes workspace")

    return candidate


def resolve_clone_target(url: str, destination: str | None = None) -> str:
    resolved_destination = _resolve_clone_destination(destination)
    if resolved_destination:
        return resolved_destination

    stripped_url = url.rstrip("/")
    repo_name = stripped_url.split("/")[-1].split(":")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]
    if not repo_name:
        raise OperationError("Unable to infer repository name from URL")

    return str(Path(WORKSPACE) / repo_name)


def _run(cmd: list[str], cwd: str | None = None) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        raise OperationError(result.stderr.strip() or "Command failed")
    return result.stdout


def clone_repo(url: str, destination: str | None = None) -> str:
    resolved_destination = _resolve_clone_destination(destination)
    payload = {"url": url}
    if destination:
        payload["destination"] = destination

    events.operation_events.record("service", "clone", "started", payload)

    cmd = ["git", "clone", url]
    if resolved_destination:
        cmd.append(resolved_destination)
    output = _run(cmd, cwd=WORKSPACE)

    events.operation_events.record("service", "clone", "completed", payload)
    return output


def checkout(branch: str) -> str:
    events.operation_events.record("service", "checkout", "started", {"branch": branch})
    output = _run(["git", "checkout", branch], cwd=WORKSPACE)
    events.operation_events.record("service", "checkout", "completed", {"branch": branch})
    return output


def commit(message: str) -> str:
    events.operation_events.record("service", "commit", "started", {"message": message})
    _run(["git", "add", "."], cwd=WORKSPACE)
    output = _run(["git", "commit", "-m", message], cwd=WORKSPACE)
    events.operation_events.record("service", "commit", "completed", {"message": message})
    return output


def push(remote: str = "origin", branch: str = "main") -> str:
    events.operation_events.record(
        "service", "push", "started", {"remote": remote, "branch": branch}
    )
    output = _run(["git", "push", remote, branch], cwd=WORKSPACE)
    events.operation_events.record(
        "service", "push", "completed", {"remote": remote, "branch": branch}
    )
    return output


def exec_cmd(cmd: str) -> str:
    events.operation_events.record("service", "exec", "started", {"cmd": cmd})
    output = _run(shlex.split(cmd), cwd=WORKSPACE)
    events.operation_events.record("service", "exec", "completed", {"cmd": cmd})
    return output
