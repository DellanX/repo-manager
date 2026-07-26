import pytest
from pydantic import ValidationError
from src.models.schemas import (
    CheckoutRequest,
    CloneRequest,
    CommitRequest,
    CredentialCreateRequest,
    CredentialUpdateRequest,
    ExecRequest,
    MCPCallRequest,
    PushRequest,
    WriteFileRequest,
)


def test_t_schema_push_defaults() -> None:
    """T-SCHEMA-PUSH-DEFAULTS"""
    model = PushRequest()
    assert model.remote == "origin"
    assert model.branch == "main"


def test_t_schema_mcp_args_default_empty_object() -> None:
    """T-SCHEMA-MCP-ARGS-DEFAULT"""
    model = MCPCallRequest(tool="git.clone")
    assert model.args == {}


def test_t_schema_required_field_validation() -> None:
    """T-SCHEMA-REQUIRED-VALIDATION"""
    with pytest.raises(ValidationError, match="tool"):
        MCPCallRequest()


def test_t_schema_clone_request_requires_url() -> None:
    """T-SCHEMA-CLONE-REQUIRED: CloneRequest requires url field."""
    with pytest.raises(ValidationError, match="url"):
        CloneRequest()


def test_t_schema_checkout_request_requires_branch() -> None:
    """T-SCHEMA-CHECKOUT-REQUIRED: CheckoutRequest requires branch field."""
    with pytest.raises(ValidationError, match="branch"):
        CheckoutRequest()


def test_t_schema_commit_request_requires_message() -> None:
    """T-SCHEMA-COMMIT-REQUIRED: CommitRequest requires message field."""
    with pytest.raises(ValidationError, match="message"):
        CommitRequest()


def test_t_schema_write_file_request_requires_path_and_content() -> None:
    """T-SCHEMA-WRITE-REQUIRED: WriteFileRequest requires path and content fields."""
    with pytest.raises(ValidationError) as exc_info:
        WriteFileRequest()
    error_str = str(exc_info.value)
    assert "path" in error_str
    assert "content" in error_str


def test_t_schema_exec_request_requires_cmd() -> None:
    """T-SCHEMA-EXEC-REQUIRED: ExecRequest requires cmd field."""
    with pytest.raises(ValidationError, match="cmd"):
        ExecRequest()


def test_t_schema_all_models_accept_valid_data() -> None:
    """T-SCHEMA-VALID-DATA: All models accept valid data."""
    assert (
        CloneRequest(url="https://github.com/test/repo.git").url
        == "https://github.com/test/repo.git"
    )
    assert CheckoutRequest(branch="main").branch == "main"
    assert CommitRequest(message="test commit").message == "test commit"
    assert WriteFileRequest(path="test.txt", content="data").path == "test.txt"
    assert ExecRequest(cmd="git status").cmd == "git status"
    assert PushRequest(remote="upstream", branch="feature").remote == "upstream"
    clone_request = CloneRequest(
        url="https://github.com/test/repo.git",
        credential_id="cred-1",
    )
    assert clone_request.credential_id == "cred-1"
    cred_create = CredentialCreateRequest(
        name="GitLab PAT",
        provider="gitlab",
        host="gitlab.com",
        username="oauth2",
        secret="token-value",
    )
    assert cred_create.provider == "gitlab"
    cred_update = CredentialUpdateRequest(name="Updated")
    assert cred_update.name == "Updated"
