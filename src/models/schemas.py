from typing import Any

from pydantic import BaseModel, Field


class CloneRequest(BaseModel):
    url: str


class CheckoutRequest(BaseModel):
    branch: str


class CommitRequest(BaseModel):
    message: str


class PushRequest(BaseModel):
    remote: str = "origin"
    branch: str = "main"


class ReadFileRequest(BaseModel):
    path: str


class WriteFileRequest(BaseModel):
    path: str
    content: str


class ExecRequest(BaseModel):
    cmd: str


class MCPCallRequest(BaseModel):
    tool: str = Field(..., description="MCP tool name")
    args: dict[str, Any] = Field(default_factory=dict)
