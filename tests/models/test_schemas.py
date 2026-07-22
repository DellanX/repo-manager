from pydantic import ValidationError

from src.models.schemas import (
    CheckoutRequest,
    CloneRequest,
    CommitRequest,
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
    try:
        MCPCallRequest()
        assert False, "Expected validation error"
    except ValidationError as exc:
        assert "tool" in str(exc)


def test_t_schema_clone_request_requires_url() -> None:
    """T-SCHEMA-CLONE-REQUIRED: CloneRequest requires url field."""
    try:
        CloneRequest()
        assert False, "Expected validation error"
    except ValidationError as exc:
        assert "url" in str(exc)


def test_t_schema_checkout_request_requires_branch() -> None:
    """T-SCHEMA-CHECKOUT-REQUIRED: CheckoutRequest requires branch field."""
    try:
        CheckoutRequest()
        assert False, "Expected validation error"
    except ValidationError as exc:
        assert "branch" in str(exc)


def test_t_schema_commit_request_requires_message() -> None:
    """T-SCHEMA-COMMIT-REQUIRED: CommitRequest requires message field."""
    try:
        CommitRequest()
        assert False, "Expected validation error"
    except ValidationError as exc:
        assert "message" in str(exc)


def test_t_schema_write_file_request_requires_path_and_content() -> None:
    """T-SCHEMA-WRITE-REQUIRED: WriteFileRequest requires path and content fields."""
    try:
        WriteFileRequest()
        assert False, "Expected validation error"
    except ValidationError as exc:
        error_str = str(exc)
        assert "path" in error_str
        assert "content" in error_str


def test_t_schema_exec_request_requires_cmd() -> None:
    """T-SCHEMA-EXEC-REQUIRED: ExecRequest requires cmd field."""
    try:
        ExecRequest()
        assert False, "Expected validation error"
    except ValidationError as exc:
        assert "cmd" in str(exc)


def test_t_schema_all_models_accept_valid_data() -> None:
    """T-SCHEMA-VALID-DATA: All models accept valid data."""
    assert CloneRequest(url="https://github.com/test/repo.git").url == "https://github.com/test/repo.git"
    assert CheckoutRequest(branch="main").branch == "main"
    assert CommitRequest(message="test commit").message == "test commit"
    assert WriteFileRequest(path="test.txt", content="data").path == "test.txt"
    assert ExecRequest(cmd="git status").cmd == "git status"
    assert PushRequest(remote="upstream", branch="feature").remote == "upstream"
