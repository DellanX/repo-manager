from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

from src.models.schemas import MCPCallRequest
from src.services.credential_store import (
    CredentialStoreError,
    credential_store,
    list_secret_drivers,
)
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
from src.services.ssh_identity_store import SSHIdentityStoreError, ssh_identity_store

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
    if "credential_id" in args and "ssh_identity_id" in args:
        raise OperationError("Provide either credential_id or ssh_identity_id, not both")
    credential = None
    ssh_identity_file = None
    if "credential_id" in args:
        credential = credential_store.get_credential_for_use(str(args["credential_id"]), url)
    if "ssh_identity_id" in args:
        identity = ssh_identity_store.get_identity_for_use(str(args["ssh_identity_id"]), url)
        ssh_identity_file = identity.identity_file
    output = clone_repo(url, destination_value, credential=credential, ssh_identity_file=ssh_identity_file)
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


def _credential_drivers(args: dict[str, Any]) -> dict[str, object]:
    del args
    return {
        "active_driver": credential_store.secret_driver_name,
        "drivers": list_secret_drivers(),
    }


def _ssh_identity_payload(item: Any) -> dict[str, str | bool | None]:
    return {
        "identity_id": item.identity_id,
        "name": item.name,
        "host": item.host,
        "username": item.username,
        "identity_file": item.identity_file,
        "public_key": item.public_key,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "revoked_at": item.revoked_at,
        "is_active": item.is_active,
    }


def _ssh_identity_list(args: dict[str, Any]) -> dict[str, list[dict[str, str | bool | None]]]:
    del args
    items = ssh_identity_store.list_identities()
    return {"ssh_identities": [_ssh_identity_payload(item) for item in items]}


def _ssh_identity_create(args: dict[str, Any]) -> dict[str, str | bool | None]:
    item = ssh_identity_store.create_identity(
        name=str(args["name"]),
        host=str(args["host"]),
        username=str(args.get("username", "git")),
    )
    return _ssh_identity_payload(item)


def _ssh_identity_revoke(args: dict[str, Any]) -> dict[str, str | bool | None]:
    item = ssh_identity_store.revoke_identity(str(args["identity_id"]))
    return _ssh_identity_payload(item)


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
    "credentials.drivers": {"fn": _credential_drivers, "description": "List secret storage drivers"},
    "ssh_identities.list": {"fn": _ssh_identity_list, "description": "List SSH identities"},
    "ssh_identities.create": {"fn": _ssh_identity_create, "description": "Create SSH identity"},
    "ssh_identities.revoke": {"fn": _ssh_identity_revoke, "description": "Revoke SSH identity"},
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
    except (OperationError, CredentialStoreError, SSHIdentityStoreError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
