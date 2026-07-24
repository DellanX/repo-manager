from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

from src.models.schemas import MCPCallRequest
from src.services.file_operations import read_file, write_file
from src.services.git_operations import OperationError, checkout, clone_repo, commit, exec_cmd, push

router = APIRouter(prefix="/mcp", tags=["mcp"])


def _clone(args: dict[str, Any]) -> dict[str, str]:
    return {"output": clone_repo(str(args["url"]))}


def _checkout(args: dict[str, Any]) -> dict[str, str]:
    return {"output": checkout(str(args["branch"]))}


def _commit(args: dict[str, Any]) -> dict[str, str]:
    return {"output": commit(str(args["message"]))}


def _push(args: dict[str, Any]) -> dict[str, str]:
    remote = str(args.get("remote", "origin"))
    branch = str(args.get("branch", "main"))
    return {"output": push(remote, branch)}


def _read_file(args: dict[str, Any]) -> dict[str, str]:
    return {"content": read_file(str(args["path"]))}


def _write_file(args: dict[str, Any]) -> dict[str, str]:
    return write_file(str(args["path"]), str(args.get("content", "")))


def _exec(args: dict[str, Any]) -> dict[str, str]:
    return {"output": exec_cmd(str(args["cmd"]))}


ToolFn = Callable[[dict[str, Any]], dict[str, str]]

TOOLS: dict[str, dict[str, Any]] = {
    "git.clone": {"fn": _clone, "description": "Clone a git repository"},
    "git.checkout": {"fn": _checkout, "description": "Checkout a branch"},
    "git.commit": {"fn": _commit, "description": "Commit workspace changes"},
    "git.push": {"fn": _push, "description": "Push to a remote branch"},
    "workspace.read_file": {"fn": _read_file, "description": "Read a file from workspace"},
    "workspace.write_file": {"fn": _write_file, "description": "Write a file in workspace"},
    "workspace.exec": {"fn": _exec, "description": "Execute a command in workspace"},
}


@router.get("/tools")
def list_tools() -> dict[str, list[dict[str, str]]]:
    return {
        "tools": [
            {"name": name, "description": str(meta["description"])} for name, meta in TOOLS.items()
        ]
    }


@router.post("/call")
def call_tool(request: MCPCallRequest) -> dict[str, Any]:
    entry = TOOLS.get(request.tool)
    if not entry:
        raise HTTPException(status_code=404, detail="Unknown MCP tool")

    try:
        fn: ToolFn = entry["fn"]
        result = fn(request.args)
        return {"tool": request.tool, "ok": True, "result": result}
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Missing argument: {exc.args[0]}") from exc
    except OperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
