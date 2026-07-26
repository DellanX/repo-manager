import pytest
from src.services.git_operations import OperationError


def _mock_workspace_lookup(monkeypatch: pytest.MonkeyPatch, path: str = "/workspace/ws-1") -> None:
    monkeypatch.setattr(
        "src.api.mcp.inventory_service.require_workspace",
        lambda workspace_id: type("Workspace", (), {"workspace_id": workspace_id, "path": path})(),
    )


def test_t_mcp_tools_lists_registry(client) -> None:
    """T-MCP-TOOLS-LIST-200"""
    resp = client.get("/api/v1/mcp/tools")
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
        "credentials.list",
        "credentials.create",
        "credentials.update",
        "credentials.revoke",
        "credentials.drivers",
        "ssh_identities.list",
        "ssh_identities.create",
        "ssh_identities.revoke",
    }


def test_t_mcp_git_clone_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-GIT-CLONE-200"""
    monkeypatch.setattr("src.api.mcp.resolve_clone_target", lambda url, destination=None: "/tmp/repo")
    monkeypatch.setattr(
        "src.api.mcp.inventory_service.register_cloned_repository",
        lambda root_path, origin_url: None,
    )
    monkeypatch.setattr("src.api.mcp.inventory_service.find_workspace_by_path", lambda path: None)
    monkeypatch.setattr(
        "src.api.mcp.clone_repo",
        lambda url, destination=None, credential=None, ssh_identity_file=None: "ok",
    )
    resp = client.post("/api/v1/mcp/call", json={"tool": "git.clone", "args": {"url": "u"}})
    assert resp.status_code == 200
    assert resp.json() == {"tool": "git.clone", "ok": True, "result": {"output": "ok"}}


def test_t_mcp_git_clone_destination_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-GIT-CLONE-DEST-200"""
    captured = {}
    monkeypatch.setattr("src.api.mcp.resolve_clone_target", lambda url, destination=None: "/tmp/repo")
    monkeypatch.setattr(
        "src.api.mcp.inventory_service.register_cloned_repository",
        lambda root_path, origin_url: None,
    )
    monkeypatch.setattr("src.api.mcp.inventory_service.find_workspace_by_path", lambda path: None)

    def fake_clone(
        url: str,
        destination: str | None = None,
        credential=None,
        ssh_identity_file=None,
    ) -> str:
        captured["url"] = url
        captured["destination"] = destination
        return "ok"

    monkeypatch.setattr("src.api.mcp.clone_repo", fake_clone)
    resp = client.post(
        "/api/v1/mcp/call",
        json={
            "tool": "git.clone",
            "args": {"url": "u", "destination": "repos/repo-manager-copy"},
        },
    )
    assert resp.status_code == 200
    assert captured == {"url": "u", "destination": "repos/repo-manager-copy"}


def test_t_mcp_git_clone_with_credential_id_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-GIT-CLONE-CREDENTIAL-ID-200"""
    captured = {}
    monkeypatch.setattr("src.api.mcp.resolve_clone_target", lambda url, destination=None: "/tmp/repo")
    monkeypatch.setattr(
        "src.api.mcp.inventory_service.register_cloned_repository",
        lambda root_path, origin_url: None,
    )
    monkeypatch.setattr("src.api.mcp.inventory_service.find_workspace_by_path", lambda path: None)

    class DummyCredential:
        credential_id = "cred-1"
        provider = "gitlab"
        host = "gitlab.com"
        username = "oauth2"
        secret = "token-value"

    monkeypatch.setattr(
        "src.api.mcp.credential_store.get_credential_for_use",
        lambda credential_id, url: DummyCredential(),
    )

    def fake_clone(
        url: str,
        destination: str | None = None,
        credential=None,
        ssh_identity_file=None,
    ) -> str:
        captured["url"] = url
        captured["destination"] = destination
        captured["credential"] = credential
        return "ok"

    monkeypatch.setattr("src.api.mcp.clone_repo", fake_clone)
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "git.clone", "args": {"url": "u", "credential_id": "cred-1"}},
    )
    assert resp.status_code == 200
    assert captured["credential"].credential_id == "cred-1"


def test_t_mcp_git_clone_with_ssh_identity_id_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-GIT-CLONE-SSH-IDENTITY-ID-200"""
    captured = {}
    monkeypatch.setattr("src.api.mcp.resolve_clone_target", lambda url, destination=None: "/tmp/repo")
    monkeypatch.setattr(
        "src.api.mcp.inventory_service.register_cloned_repository",
        lambda root_path, origin_url: None,
    )
    monkeypatch.setattr("src.api.mcp.inventory_service.find_workspace_by_path", lambda path: None)

    class DummyIdentity:
        identity_id = "ssh-1"
        host = "gitlab.com"
        username = "git"
        identity_file = "C:/keys/ssh-1"

    monkeypatch.setattr(
        "src.api.mcp.ssh_identity_store.get_identity_for_use",
        lambda identity_id, url: DummyIdentity(),
    )

    def fake_clone(
        url: str,
        destination: str | None = None,
        credential=None,
        ssh_identity_file=None,
    ) -> str:
        captured["credential"] = credential
        captured["ssh_identity_file"] = ssh_identity_file
        return "ok"

    monkeypatch.setattr("src.api.mcp.clone_repo", fake_clone)
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "git.clone", "args": {"url": "git@gitlab.com:group/repo.git", "ssh_identity_id": "ssh-1"}},
    )
    assert resp.status_code == 200
    assert captured["credential"] is None
    assert captured["ssh_identity_file"] == "C:/keys/ssh-1"


def test_t_mcp_push_defaults(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-GIT-PUSH-DEFAULTS"""
    called = {}
    _mock_workspace_lookup(monkeypatch)

    def fake_push(workspace_root: str, remote: str, branch: str) -> str:
        called["workspace_root"] = workspace_root
        called["remote"] = remote
        called["branch"] = branch
        return "ok"

    monkeypatch.setattr("src.api.mcp.push", fake_push)
    resp = client.post("/api/v1/mcp/call", json={"tool": "git.push", "args": {"workspace_id": "ws-1"}})
    assert resp.status_code == 200
    assert called == {"workspace_root": "/workspace/ws-1", "remote": "origin", "branch": "main"}


def test_t_mcp_unknown_tool_404(client) -> None:
    """T-MCP-UNKNOWN-404"""
    resp = client.post("/api/v1/mcp/call", json={"tool": "bad.tool", "args": {}})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Unknown MCP tool"


def test_t_mcp_missing_argument_400(client) -> None:
    """T-MCP-MISSING-ARG-400"""
    resp = client.post("/api/v1/mcp/call", json={"tool": "git.checkout", "args": {}})
    assert resp.status_code == 400
    assert "Missing argument" in resp.json()["detail"]


def test_t_mcp_operation_error_400(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-OP-ERROR-400"""

    def fail(url: str, destination: str | None = None, credential=None, ssh_identity_file=None) -> str:
        raise OperationError("boom")

    monkeypatch.setattr("src.api.mcp.clone_repo", fail)
    resp = client.post("/api/v1/mcp/call", json={"tool": "git.clone", "args": {"url": "u"}})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "boom"


def test_t_mcp_clone_registers_inventory(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-CLONE-INV-REGISTER"""
    captured = {}

    monkeypatch.setattr(
        "src.api.mcp.clone_repo",
        lambda url, destination=None, credential=None, ssh_identity_file=None: "ok",
    )
    monkeypatch.setattr(
        "src.api.mcp.resolve_clone_target",
        lambda url, destination=None: "/workspace/repo-manager-copy",
    )

    def fake_register(root_path: str, origin_url: str) -> None:
        captured["root_path"] = root_path
        captured["origin_url"] = origin_url

    monkeypatch.setattr("src.api.mcp.inventory_service.register_cloned_repository", fake_register)
    monkeypatch.setattr("src.api.mcp.inventory_service.find_workspace_by_path", lambda path: None)

    resp = client.post("/api/v1/mcp/call", json={"tool": "git.clone", "args": {"url": "u"}})
    assert resp.status_code == 200
    assert captured == {"root_path": "/workspace/repo-manager-copy", "origin_url": "u"}


def test_t_mcp_clone_returns_workspace_id_when_available(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-CLONE-WORKSPACE-ID-200"""
    monkeypatch.setattr(
        "src.api.mcp.clone_repo",
        lambda url, destination=None, credential=None, ssh_identity_file=None: "ok",
    )
    monkeypatch.setattr("src.api.mcp.resolve_clone_target", lambda url, destination=None: "/workspace/repo")
    monkeypatch.setattr(
        "src.api.mcp.inventory_service.register_cloned_repository",
        lambda root_path, origin_url: None,
    )
    monkeypatch.setattr(
        "src.api.mcp.inventory_service.find_workspace_by_path",
        lambda path: type("Workspace", (), {"workspace_id": "ws-1", "path": path})(),
    )

    resp = client.post("/api/v1/mcp/call", json={"tool": "git.clone", "args": {"url": "u"}})
    assert resp.status_code == 200
    assert resp.json() == {
        "tool": "git.clone",
        "ok": True,
        "result": {"output": "ok", "workspace_id": "ws-1"},
    }


def test_t_mcp_handler_casts_values_to_string(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-ARG-STRING-CAST"""
    captured = {}
    _mock_workspace_lookup(monkeypatch)

    def fake_checkout(branch: str, workspace_root: str) -> str:
        captured["type"] = type(branch)
        captured["value"] = branch
        return "ok"

    monkeypatch.setattr("src.api.mcp.checkout", fake_checkout)
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "git.checkout", "args": {"workspace_id": "ws-1", "branch": 123}},
    )
    assert resp.status_code == 200
    assert captured == {"type": str, "value": "123"}


def test_t_mcp_git_commit_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-GIT-COMMIT-200"""
    _mock_workspace_lookup(monkeypatch)
    monkeypatch.setattr("src.api.mcp.commit", lambda msg, workspace_root: "committed")
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "git.commit", "args": {"workspace_id": "ws-1", "message": "test"}},
    )
    assert resp.status_code == 200
    assert resp.json() == {"tool": "git.commit", "ok": True, "result": {"output": "committed"}}


def test_t_mcp_read_file_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-READ-FILE-200"""
    _mock_workspace_lookup(monkeypatch)
    monkeypatch.setattr("src.api.mcp.read_file", lambda path, workspace_root: "file content")
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "workspace.read_file", "args": {"workspace_id": "ws-1", "path": "test.txt"}},
    )
    assert resp.status_code == 200
    result = {"tool": "workspace.read_file", "ok": True, "result": {"content": "file content"}}
    assert resp.json() == result


def test_t_mcp_write_file_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-WRITE-FILE-200"""
    _mock_workspace_lookup(monkeypatch)
    monkeypatch.setattr("src.api.mcp.write_file", lambda path, content, workspace_root: {"status": "ok"})
    resp = client.post(
        "/api/v1/mcp/call",
        json={
            "tool": "workspace.write_file",
            "args": {"workspace_id": "ws-1", "path": "out.txt", "content": "data"},
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {"tool": "workspace.write_file", "ok": True, "result": {"status": "ok"}}


def test_t_mcp_exec_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-EXEC-200"""
    _mock_workspace_lookup(monkeypatch)
    monkeypatch.setattr("src.api.mcp.exec_cmd", lambda cmd, workspace_root: "result")
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "workspace.exec", "args": {"workspace_id": "ws-1", "cmd": "ls"}},
    )
    assert resp.status_code == 200
    assert resp.json() == {"tool": "workspace.exec", "ok": True, "result": {"output": "result"}}


def test_t_mcp_git_checkout_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-GIT-CHECKOUT-200"""
    _mock_workspace_lookup(monkeypatch)
    monkeypatch.setattr("src.api.mcp.checkout", lambda branch, workspace_root: "ok")
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "git.checkout", "args": {"workspace_id": "ws-1", "branch": "main"}},
    )
    assert resp.status_code == 200
    assert resp.json() == {"tool": "git.checkout", "ok": True, "result": {"output": "ok"}}


def test_t_mcp_workspace_read_file_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-WORKSPACE-READ-200"""
    _mock_workspace_lookup(monkeypatch)
    monkeypatch.setattr("src.api.mcp.read_file", lambda path, workspace_root: "file content")
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "workspace.read_file", "args": {"workspace_id": "ws-1", "path": "test.txt"}},
    )
    assert resp.status_code == 200
    expected = {"tool": "workspace.read_file", "ok": True, "result": {"content": "file content"}}
    assert resp.json() == expected


def test_t_mcp_workspace_write_file_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-WORKSPACE-WRITE-200"""
    _mock_workspace_lookup(monkeypatch)
    monkeypatch.setattr("src.api.mcp.write_file", lambda path, content, workspace_root: {"status": "ok"})
    resp = client.post(
        "/api/v1/mcp/call",
        json={
            "tool": "workspace.write_file",
            "args": {"workspace_id": "ws-1", "path": "test.txt", "content": "data"},
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {"tool": "workspace.write_file", "ok": True, "result": {"status": "ok"}}


def test_t_mcp_workspace_exec_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-WORKSPACE-EXEC-200"""
    _mock_workspace_lookup(monkeypatch)
    monkeypatch.setattr("src.api.mcp.exec_cmd", lambda cmd, workspace_root: "done")
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "workspace.exec", "args": {"workspace_id": "ws-1", "cmd": "ls"}},
    )
    assert resp.status_code == 200
    assert resp.json() == {"tool": "workspace.exec", "ok": True, "result": {"output": "done"}}


def test_t_mcp_credentials_list_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-CREDENTIALS-LIST-200"""
    monkeypatch.setattr(
        "src.api.mcp.credential_store.list_credentials",
        lambda: [
            type(
                "Meta",
                (),
                {
                    "credential_id": "cred-1",
                    "name": "GitLab PAT",
                    "provider": "gitlab",
                    "host": "gitlab.com",
                    "username": "oauth2",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "revoked_at": None,
                    "is_active": True,
                },
            )()
        ],
    )
    resp = client.post("/api/v1/mcp/call", json={"tool": "credentials.list", "args": {}})
    assert resp.status_code == 200
    assert resp.json()["result"]["credentials"][0]["credential_id"] == "cred-1"
    assert "secret" not in resp.json()["result"]["credentials"][0]


def test_t_mcp_credentials_create_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-CREDENTIALS-CREATE-200"""
    monkeypatch.setattr(
        "src.api.mcp.credential_store.create_credential",
        lambda name, provider, host, username, secret: type(
            "Meta",
            (),
            {
                "credential_id": "cred-1",
                "name": name,
                "provider": provider,
                "host": host,
                "username": username,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "revoked_at": None,
                "is_active": True,
            },
        )(),
    )
    resp = client.post(
        "/api/v1/mcp/call",
        json={
            "tool": "credentials.create",
            "args": {
                "name": "GitLab PAT",
                "provider": "gitlab",
                "host": "gitlab.com",
                "username": "oauth2",
                "secret": "token-value",
            },
        },
    )
    assert resp.status_code == 200
    assert resp.json()["result"]["credential_id"] == "cred-1"


def test_t_mcp_credentials_revoke_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-CREDENTIALS-REVOKE-200"""
    monkeypatch.setattr(
        "src.api.mcp.credential_store.revoke_credential",
        lambda credential_id: type(
            "Meta",
            (),
            {
                "credential_id": credential_id,
                "name": "GitLab PAT",
                "provider": "gitlab",
                "host": "gitlab.com",
                "username": "oauth2",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
                "revoked_at": "2026-01-02T00:00:00Z",
                "is_active": False,
            },
        )(),
    )
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "credentials.revoke", "args": {"credential_id": "cred-1"}},
    )
    assert resp.status_code == 200
    assert resp.json()["result"]["is_active"] is False


def test_t_mcp_credentials_drivers_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-CREDENTIALS-DRIVERS-200"""
    monkeypatch.setattr("src.api.mcp.credential_store.secret_driver_name", "keyring")
    monkeypatch.setattr(
        "src.api.mcp.list_secret_drivers",
        lambda: [{"name": "keyring", "is_secure": True}],
    )
    resp = client.post("/api/v1/mcp/call", json={"tool": "credentials.drivers", "args": {}})
    assert resp.status_code == 200
    assert resp.json()["result"]["active_driver"] == "keyring"


def test_t_mcp_ssh_identities_create_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-MCP-SSH-IDENTITY-CREATE-200"""
    monkeypatch.setattr(
        "src.api.mcp.ssh_identity_store.create_identity",
        lambda name, host, username: type(
            "Meta",
            (),
            {
                "identity_id": "ssh-1",
                "name": name,
                "host": host,
                "username": username,
                "identity_file": "C:/keys/ssh-1",
                "public_key": "ssh-ed25519 AAAAB3Nza...",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "revoked_at": None,
                "is_active": True,
            },
        )(),
    )
    resp = client.post(
        "/api/v1/mcp/call",
        json={"tool": "ssh_identities.create", "args": {"name": "GitLab Key", "host": "gitlab.com"}},
    )
    assert resp.status_code == 200
    assert resp.json()["result"]["identity_id"] == "ssh-1"
