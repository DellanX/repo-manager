from fastapi import APIRouter, HTTPException

from src.models.schemas import (
    CheckoutRequest,
    CloneRequest,
    CommitRequest,
    ExecRequest,
    PushRequest,
    WriteFileRequest,
)
from src.services.file_operations import read_file, write_file
from src.services.git_operations import OperationError, checkout, clone_repo, commit, exec_cmd, push

router = APIRouter(tags=["rest"])


@router.post("/clone")
def clone_repo_route(request: CloneRequest) -> dict[str, str]:
    try:
        return {"output": clone_repo(request.url)}
    except OperationError as exc:
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
