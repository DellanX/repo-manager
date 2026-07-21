import os

from src.core.config import WORKSPACE
from src.core.events import operation_events
from src.services.git_operations import OperationError


def _resolve_workspace_path(path: str) -> str:
    full = os.path.abspath(os.path.join(WORKSPACE, path))
    workspace_root = os.path.abspath(WORKSPACE)
    if full != workspace_root and not full.startswith(workspace_root + os.sep):
        raise OperationError("Path escapes workspace")
    return full


def read_file(path: str) -> str:
    full = _resolve_workspace_path(path)
    if not os.path.exists(full):
        raise OperationError("File not found")

    operation_events.record("service", "read_file", "completed", {"path": path})
    with open(full, "r", encoding="utf-8") as handle:
        return handle.read()


def write_file(path: str, content: str) -> dict[str, str]:
    full = _resolve_workspace_path(path)
    os.makedirs(os.path.dirname(full), exist_ok=True)

    with open(full, "w", encoding="utf-8") as handle:
        handle.write(content)

    operation_events.record("service", "write_file", "completed", {"path": path})
    return {"status": "ok"}
