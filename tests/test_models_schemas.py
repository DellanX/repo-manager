from pydantic import ValidationError

from src.models.schemas import MCPCallRequest, PushRequest


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
