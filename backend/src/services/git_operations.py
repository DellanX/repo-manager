import os
import shlex
import subprocess
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from src.core import events
from src.core.config import WORKSPACE
from src.services.credential_store import CredentialForUse


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


def _redact_value(text: str, value: str) -> str:
    if not value:
        return text
    return text.replace(value, "***REDACTED***")


def _sanitize_output(output: str, redacted_values: list[str] | None = None) -> str:
    cleaned = output
    for value in redacted_values or []:
        cleaned = _redact_value(cleaned, value)
    return cleaned


def _run(
    cmd: list[str],
    cwd: str | None = None,
    redacted_values: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        stderr = _sanitize_output(result.stderr.strip(), redacted_values)
        raise OperationError(stderr or "Command failed")
    return _sanitize_output(result.stdout, redacted_values)


def _build_authenticated_url(url: str, credential: CredentialForUse) -> str:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise OperationError("Credential-backed clone requires an HTTP(S) URL")
    if parsed.hostname is None:
        raise OperationError("Clone URL must include a host")
    if parsed.username is not None or parsed.password is not None:
        raise OperationError("Clone URL must not include embedded credentials")

    host = parsed.hostname
    if parsed.port is not None:
        host = f"{host}:{parsed.port}"
    username = quote(credential.username, safe="")
    secret = quote(credential.secret, safe="")
    netloc = f"{username}:{secret}@{host}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def clone_repo(
    url: str,
    destination: str | None = None,
    credential: CredentialForUse | None = None,
    ssh_identity_file: str | None = None,
) -> str:
    if credential is not None and ssh_identity_file is not None:
        raise OperationError("Clone cannot use both token credential and SSH identity")

    resolved_destination = _resolve_clone_destination(destination)
    payload = {"url": url}
    if destination:
        payload["destination"] = destination
    if credential is not None:
        payload["credential_id"] = credential.credential_id
    redacted_values: list[str] | None = None
    env = None

    events.operation_events.record("service", "clone", "started", payload)

    clone_url = url
    if credential is not None:
        clone_url = _build_authenticated_url(url, credential)
        redacted_values = [credential.secret, clone_url]
    if ssh_identity_file is not None:
        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = (
            f'ssh -i "{ssh_identity_file}" '
            "-o IdentitiesOnly=yes "
            "-o StrictHostKeyChecking=accept-new"
        )
    cmd = ["git", "clone", clone_url]
    if resolved_destination:
        cmd.append(resolved_destination)
    output = _run(cmd, cwd=WORKSPACE, redacted_values=redacted_values, env=env)

    events.operation_events.record("service", "clone", "completed", payload)
    return output


def checkout(branch: str, workspace_root: str) -> str:
    events.operation_events.record(
        "service", "checkout", "started", {"branch": branch, "workspace_root": workspace_root}
    )
    output = _run(["git", "-C", workspace_root, "checkout", branch])
    events.operation_events.record(
        "service", "checkout", "completed", {"branch": branch, "workspace_root": workspace_root}
    )
    return output


def commit(message: str, workspace_root: str) -> str:
    events.operation_events.record(
        "service", "commit", "started", {"message": message, "workspace_root": workspace_root}
    )
    _run(["git", "-C", workspace_root, "add", "."])
    output = _run(["git", "-C", workspace_root, "commit", "-m", message])
    events.operation_events.record(
        "service", "commit", "completed", {"message": message, "workspace_root": workspace_root}
    )
    return output


def push(workspace_root: str, remote: str = "origin", branch: str = "main") -> str:
    events.operation_events.record(
        "service",
        "push",
        "started",
        {"remote": remote, "branch": branch, "workspace_root": workspace_root},
    )
    output = _run(["git", "-C", workspace_root, "push", remote, branch])
    events.operation_events.record(
        "service",
        "push",
        "completed",
        {"remote": remote, "branch": branch, "workspace_root": workspace_root},
    )
    return output


def exec_cmd(cmd: str, workspace_root: str) -> str:
    events.operation_events.record(
        "service", "exec", "started", {"cmd": cmd, "workspace_root": workspace_root}
    )
    output = _run(shlex.split(cmd), cwd=workspace_root)
    events.operation_events.record(
        "service", "exec", "completed", {"cmd": cmd, "workspace_root": workspace_root}
    )
    return output
