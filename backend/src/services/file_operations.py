import os

from src.core import events
from src.services.git_operations import OperationError


def _resolve_workspace_path(workspace_root: str, path: str) -> str:
    full = os.path.abspath(os.path.join(workspace_root, path))
    normalized_workspace_root = os.path.abspath(workspace_root)
    if not os.path.isdir(normalized_workspace_root):
        raise OperationError("Workspace path missing")
    if full != normalized_workspace_root and not full.startswith(normalized_workspace_root + os.sep):
        raise OperationError("Path escapes workspace")
    return full


def read_file(path: str, workspace_root: str) -> str:
    full = _resolve_workspace_path(workspace_root, path)
    if not os.path.exists(full):
        raise OperationError("File not found")

    events.operation_events.record(
        "service", "read_file", "completed", {"path": path, "workspace_root": workspace_root}
    )
    with open(full, encoding="utf-8") as handle:
        return handle.read()


def write_file(path: str, content: str, workspace_root: str) -> dict[str, str]:
    full = _resolve_workspace_path(workspace_root, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)

    with open(full, "w", encoding="utf-8") as handle:
        handle.write(content)

    events.operation_events.record(
        "service", "write_file", "completed", {"path": path, "workspace_root": workspace_root}
    )
    return {"status": "ok"}
