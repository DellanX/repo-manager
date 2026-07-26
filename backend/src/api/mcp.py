from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

from src.models.schemas import MCPCallRequest
from src.services.credential_store import CredentialStoreError, credential_store
from src.services.file_operations import read_file, write_file
from src.services.git_operations import (
    OperationError,
    checkout,
    clone_repo,
    commit,
    exec_cmd,
    push,
    resolve_clone_target,
)
from src.services.workspace_inventory import inventory_service

router = APIRouter(prefix="/mcp", tags=["mcp"])


def _credential_payload(item: Any) -> dict[str, str | bool | None]:
    return {
        "credential_id": item.credential_id,
        "name": item.name,
        "provider": item.provider,
        "host": item.host,
        "username": item.username,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "revoked_at": item.revoked_at,
        "is_active": item.is_active,
    }


def _clone(args: dict[str, Any]) -> dict[str, str]:
    destination = args.get("destination")
    if destination is None and "path" in args:
        destination = args["path"]
    destination_value = None if destination is None else str(destination)
    url = str(args["url"])
    credential = None
    if "credential_id" in args:
        credential = credential_store.get_credential_for_use(str(args["credential_id"]), url)
    output = clone_repo(url, destination_value, credential=credential)
    clone_target = resolve_clone_target(url, destination_value)
    inventory_service.register_cloned_repository(
        root_path=clone_target,
        origin_url=url,
    )
    return {"output": output}


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


def _credential_list(args: dict[str, Any]) -> dict[str, list[dict[str, str | bool | None]]]:
    del args
    items = credential_store.list_credentials()
    return {"credentials": [_credential_payload(item) for item in items]}


def _credential_create(args: dict[str, Any]) -> dict[str, str | bool | None]:
    item = credential_store.create_credential(
        name=str(args["name"]),
        provider=str(args["provider"]),
        host=str(args["host"]),
        username=str(args.get("username", "oauth2")),
        secret=str(args["secret"]),
    )
    return _credential_payload(item)


def _credential_update(args: dict[str, Any]) -> dict[str, str | bool | None]:
    item = credential_store.update_credential(
        str(args["credential_id"]),
        name=None if "name" not in args else str(args["name"]),
        host=None if "host" not in args else str(args["host"]),
        username=None if "username" not in args else str(args["username"]),
        secret=None if "secret" not in args else str(args["secret"]),
    )
    return _credential_payload(item)


def _credential_revoke(args: dict[str, Any]) -> dict[str, str | bool | None]:
    item = credential_store.revoke_credential(str(args["credential_id"]))
    return _credential_payload(item)


ToolFn = Callable[[dict[str, Any]], dict[str, Any]]

TOOLS: dict[str, dict[str, Any]] = {
    "git.clone": {"fn": _clone, "description": "Clone a git repository"},
    "git.checkout": {"fn": _checkout, "description": "Checkout a branch"},
    "git.commit": {"fn": _commit, "description": "Commit workspace changes"},
    "git.push": {"fn": _push, "description": "Push to a remote branch"},
    "workspace.read_file": {"fn": _read_file, "description": "Read a file from workspace"},
    "workspace.write_file": {"fn": _write_file, "description": "Write a file in workspace"},
    "workspace.exec": {"fn": _exec, "description": "Execute a command in workspace"},
    "credentials.list": {"fn": _credential_list, "description": "List credential metadata"},
    "credentials.create": {"fn": _credential_create, "description": "Create a secure credential"},
    "credentials.update": {"fn": _credential_update, "description": "Update or rotate a credential"},
    "credentials.revoke": {"fn": _credential_revoke, "description": "Revoke a credential"},
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
    except (OperationError, CredentialStoreError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
