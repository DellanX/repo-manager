from fastapi import APIRouter, HTTPException

from src.models.schemas import (
    CheckoutRequest,
    CloneRequest,
    CommitRequest,
    CredentialCreateRequest,
    CredentialResponse,
    SecretDriverResponse,
    CredentialUpdateRequest,
    ExecRequest,
    PushRequest,
    SSHIdentityCreateRequest,
    SSHIdentityResponse,
    WriteFileRequest,
)
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
from src.services.ssh_identity_store import SSHIdentityStoreError, ssh_identity_store
from src.services.workspace_inventory import inventory_service

router = APIRouter(tags=["rest"])


@router.post("/clone")
def clone_repo_route(request: CloneRequest) -> dict[str, str]:
    try:
        if request.credential_id and request.ssh_identity_id:
            raise OperationError("Provide either credential_id or ssh_identity_id, not both")
        credential = None
        ssh_identity_file = None
        if request.credential_id:
            credential = credential_store.get_credential_for_use(request.credential_id, request.url)
        if request.ssh_identity_id:
            identity = ssh_identity_store.get_identity_for_use(request.ssh_identity_id, request.url)
            ssh_identity_file = identity.identity_file
        output = clone_repo(
            request.url,
            request.destination,
            credential=credential,
            ssh_identity_file=ssh_identity_file,
        )
        clone_target = resolve_clone_target(request.url, request.destination)
        inventory_service.register_cloned_repository(
            root_path=clone_target,
            origin_url=request.url,
        )
        return {"output": output}
    except (OperationError, CredentialStoreError, SSHIdentityStoreError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/checkout")
def checkout_route(request: CheckoutRequest) -> dict[str, str]:
    try:
        return {"output": checkout(request.branch)}
    except OperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/commit")
def commit_route(request: CommitRequest) -> dict[str, str]:
    try:
        return {"output": commit(request.message)}
    except OperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/push")
def push_route(request: PushRequest) -> dict[str, str]:
    try:
        return {"output": push(request.remote, request.branch)}
    except OperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/file")
def read_file_route(path: str) -> dict[str, str]:
    try:
        return {"content": read_file(path)}
    except OperationError as exc:
        code = 404 if str(exc) == "File not found" else 400
        raise HTTPException(status_code=code, detail=str(exc)) from exc


@router.post("/file")
def write_file_route(request: WriteFileRequest) -> dict[str, str]:
    try:
        return write_file(request.path, request.content)
    except OperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/exec")
def exec_cmd_route(request: ExecRequest) -> dict[str, str]:
    try:
        return {"output": exec_cmd(request.cmd)}
    except OperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _to_credential_response(metadata) -> CredentialResponse:
    return CredentialResponse(
        credential_id=metadata.credential_id,
        name=metadata.name,
        provider=metadata.provider,
        host=metadata.host,
        username=metadata.username,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
        revoked_at=metadata.revoked_at,
        is_active=metadata.is_active,
    )


@router.get("/credentials")
def list_credentials_route() -> dict[str, list[CredentialResponse]]:
    items = credential_store.list_credentials()
    return {"credentials": [_to_credential_response(item) for item in items]}


@router.post("/credentials")
def create_credential_route(request: CredentialCreateRequest) -> CredentialResponse:
    try:
        metadata = credential_store.create_credential(
            name=request.name,
            provider=request.provider,
            host=request.host,
            username=request.username,
            secret=request.secret,
        )
        return _to_credential_response(metadata)
    except CredentialStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/credentials/{credential_id}")
def update_credential_route(credential_id: str, request: CredentialUpdateRequest) -> CredentialResponse:
    try:
        metadata = credential_store.update_credential(
            credential_id,
            name=request.name,
            host=request.host,
            username=request.username,
            secret=request.secret,
        )
        return _to_credential_response(metadata)
    except CredentialStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/credentials/{credential_id}")
def revoke_credential_route(credential_id: str) -> CredentialResponse:
    try:
        metadata = credential_store.revoke_credential(credential_id)
        return _to_credential_response(metadata)
    except CredentialStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/credentials/drivers")
def list_credential_drivers_route() -> dict[str, object]:
    return {
        "active_driver": credential_store.secret_driver_name,
        "drivers": [SecretDriverResponse(**item) for item in list_secret_drivers()],
    }


def _to_ssh_identity_response(metadata) -> SSHIdentityResponse:
    return SSHIdentityResponse(
        identity_id=metadata.identity_id,
        name=metadata.name,
        host=metadata.host,
        username=metadata.username,
        identity_file=metadata.identity_file,
        public_key=metadata.public_key,
        created_at=metadata.created_at,
        updated_at=metadata.updated_at,
        revoked_at=metadata.revoked_at,
        is_active=metadata.is_active,
    )


@router.get("/ssh-identities")
def list_ssh_identities_route() -> dict[str, list[SSHIdentityResponse]]:
    items = ssh_identity_store.list_identities()
    return {"ssh_identities": [_to_ssh_identity_response(item) for item in items]}


@router.post("/ssh-identities")
def create_ssh_identity_route(request: SSHIdentityCreateRequest) -> SSHIdentityResponse:
    try:
        metadata = ssh_identity_store.create_identity(
            name=request.name,
            host=request.host,
            username=request.username,
        )
        return _to_ssh_identity_response(metadata)
    except SSHIdentityStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/ssh-identities/{identity_id}")
def revoke_ssh_identity_route(identity_id: str) -> SSHIdentityResponse:
    try:
        metadata = ssh_identity_store.revoke_identity(identity_id)
        return _to_ssh_identity_response(metadata)
    except SSHIdentityStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
