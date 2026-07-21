import pytest

from src.services.git_operations import OperationError


def test_t_mcp_tools_lists_registry(client) -> None:
    """T-MCP-TOOLS-LIST-200"""
    resp = client.get("/mcp/tools")
    assert resp.status_code == 200

    names = {item["name"] for item in resp.json()["tools"]}
    assert names == {
        "git.clone",
        "git.checkout",
        "git.commit",
        "git.push",
        "workspace.read_file",
        "workspace.write_file",
        "workspace.exec",
    }


def test_t_mcp_git_clone_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-GIT-CLONE-200"""
    monkeypatch.setattr("src.api.mcp.clone_repo", lambda url: "ok")
    resp = client.post("/mcp/call", json={"tool": "git.clone", "args": {"url": "u"}})
    assert resp.status_code == 200
    assert resp.json() == {"tool": "git.clone", "ok": True, "result": {"output": "ok"}}


def test_t_mcp_push_defaults(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-GIT-PUSH-DEFAULTS"""
    called = {}

    def fake_push(remote: str, branch: str) -> str:
        called["remote"] = remote
        called["branch"] = branch
        return "ok"

    monkeypatch.setattr("src.api.mcp.push", fake_push)
    resp = client.post("/mcp/call", json={"tool": "git.push", "args": {}})
    assert resp.status_code == 200
    assert called == {"remote": "origin", "branch": "main"}


def test_t_mcp_unknown_tool_404(client) -> None:
    """T-MCP-UNKNOWN-404"""
    resp = client.post("/mcp/call", json={"tool": "bad.tool", "args": {}})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Unknown MCP tool"


def test_t_mcp_missing_argument_400(client) -> None:
    """T-MCP-MISSING-ARG-400"""
    resp = client.post("/mcp/call", json={"tool": "git.checkout", "args": {}})
    assert resp.status_code == 400
    assert "Missing argument" in resp.json()["detail"]


def test_t_mcp_operation_error_400(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-OP-ERROR-400"""

    def fail(url: str) -> str:
        raise OperationError("boom")

    monkeypatch.setattr("src.api.mcp.clone_repo", fail)
    resp = client.post("/mcp/call", json={"tool": "git.clone", "args": {"url": "u"}})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "boom"


def test_t_mcp_handler_casts_values_to_string(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-ARG-STRING-CAST"""
    captured = {}

    def fake_checkout(branch: str) -> str:
        captured["type"] = type(branch)
        captured["value"] = branch
        return "ok"

    monkeypatch.setattr("src.api.mcp.checkout", fake_checkout)
    resp = client.post("/mcp/call", json={"tool": "git.checkout", "args": {"branch": 123}})
    assert resp.status_code == 200
    assert captured == {"type": str, "value": "123"}
