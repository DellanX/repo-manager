import pytest
from src.services.git_operations import OperationError


def test_t_rest_health_200(client) -> None:
    """T-REST-HEALTH-200"""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_t_rest_clone_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CLONE-200"""
    monkeypatch.setattr("src.api.rest.resolve_clone_target", lambda url, destination=None: "/tmp/repo")
    monkeypatch.setattr(
        "src.api.rest.inventory_service.register_cloned_repository",
        lambda root_path, origin_url: None,
    )
    monkeypatch.setattr(
        "src.api.rest.clone_repo",
        lambda url, destination=None, credential=None, ssh_identity_file=None: "cloned",
    )
    resp = client.post("/api/v1/clone", json={"url": "https://example/repo.git"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "cloned"}


def test_t_rest_clone_with_destination_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CLONE-DEST-200"""
    called = {}
    monkeypatch.setattr("src.api.rest.resolve_clone_target", lambda url, destination=None: "/tmp/repo")
    monkeypatch.setattr(
        "src.api.rest.inventory_service.register_cloned_repository",
        lambda root_path, origin_url: None,
    )

    def fake_clone(
        url: str,
        destination: str | None = None,
        credential=None,
        ssh_identity_file=None,
    ) -> str:
        called["url"] = url
        called["destination"] = destination
        return "cloned"

    monkeypatch.setattr("src.api.rest.clone_repo", fake_clone)
    resp = client.post(
        "/api/v1/clone",
        json={"url": "https://example/repo.git", "destination": "repos/repo-manager-copy"},
    )
    assert resp.status_code == 200
    assert called == {
        "url": "https://example/repo.git",
        "destination": "repos/repo-manager-copy",
    }


def test_t_rest_clone_with_credential_id_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CLONE-CREDENTIAL-ID-200"""
    called = {}

    class DummyCredential:
        credential_id = "cred-1"
        provider = "gitlab"
        host = "gitlab.com"
        username = "oauth2"
        secret = "token-value"

    monkeypatch.setattr(
        "src.api.rest.credential_store.get_credential_for_use",
        lambda credential_id, url: DummyCredential(),
    )
    monkeypatch.setattr("src.api.rest.resolve_clone_target", lambda url, destination=None: "/tmp/repo")
    monkeypatch.setattr(
        "src.api.rest.inventory_service.register_cloned_repository",
        lambda root_path, origin_url: None,
    )

    def fake_clone(
        url: str,
        destination: str | None = None,
        credential=None,
        ssh_identity_file=None,
    ) -> str:
        called["url"] = url
        called["destination"] = destination
        called["credential"] = credential
        called["ssh_identity_file"] = ssh_identity_file
        return "cloned"

    monkeypatch.setattr("src.api.rest.clone_repo", fake_clone)
    resp = client.post(
        "/api/v1/clone",
        json={"url": "https://gitlab.com/group/repo.git", "credential_id": "cred-1"},
    )
    assert resp.status_code == 200
    assert called["url"] == "https://gitlab.com/group/repo.git"
    assert called["destination"] is None
    assert called["credential"].credential_id == "cred-1"


def test_t_rest_clone_with_ssh_identity_id_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CLONE-SSH-IDENTITY-ID-200"""
    called = {}

    class DummyIdentity:
        identity_id = "ssh-1"
        host = "gitlab.com"
        username = "git"
        identity_file = "C:/keys/ssh-1"

    monkeypatch.setattr(
        "src.api.rest.ssh_identity_store.get_identity_for_use",
        lambda identity_id, url: DummyIdentity(),
    )
    monkeypatch.setattr("src.api.rest.resolve_clone_target", lambda url, destination=None: "/tmp/repo")
    monkeypatch.setattr(
        "src.api.rest.inventory_service.register_cloned_repository",
        lambda root_path, origin_url: None,
    )

    def fake_clone(
        url: str,
        destination: str | None = None,
        credential=None,
        ssh_identity_file=None,
    ) -> str:
        called["url"] = url
        called["destination"] = destination
        called["credential"] = credential
        called["ssh_identity_file"] = ssh_identity_file
        return "cloned"

    monkeypatch.setattr("src.api.rest.clone_repo", fake_clone)
    resp = client.post(
        "/api/v1/clone",
        json={"url": "git@gitlab.com:group/repo.git", "ssh_identity_id": "ssh-1"},
    )
    assert resp.status_code == 200
    assert called["credential"] is None
    assert called["ssh_identity_file"] == "C:/keys/ssh-1"


def test_t_rest_clone_rejects_dual_auth_400(client) -> None:
    """T-REST-CLONE-DUAL-AUTH-400"""
    resp = client.post(
        "/api/v1/clone",
        json={
            "url": "https://gitlab.com/group/repo.git",
            "credential_id": "cred-1",
            "ssh_identity_id": "ssh-1",
        },
    )
    assert resp.status_code == 400
    assert "either credential_id or ssh_identity_id" in resp.json()["detail"]


def test_t_rest_checkout_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CHECKOUT-200"""
    monkeypatch.setattr("src.api.rest.checkout", lambda branch: "ok")
    resp = client.post("/api/v1/checkout", json={"branch": "main"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "ok"}


def test_t_rest_commit_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-COMMIT-200"""
    monkeypatch.setattr("src.api.rest.commit", lambda message: "ok")
    resp = client.post("/api/v1/commit", json={"message": "m"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "ok"}


def test_t_rest_push_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-PUSH-200"""
    monkeypatch.setattr("src.api.rest.push", lambda remote, branch: "ok")
    resp = client.post("/api/v1/push", json={"remote": "origin", "branch": "main"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "ok"}


def test_t_rest_push_defaults(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-PUSH-DEFAULTS: Push uses origin/main when not specified."""
    called = {}

    def fake_push(remote: str, branch: str) -> str:
        called["remote"] = remote
        called["branch"] = branch
        return "ok"

    monkeypatch.setattr("src.api.rest.push", fake_push)
    resp = client.post("/api/v1/push", json={})
    assert resp.status_code == 200
    assert called == {"remote": "origin", "branch": "main"}


def test_t_rest_file_get_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-FILE-GET-200"""
    monkeypatch.setattr("src.api.rest.read_file", lambda path: "content")
    resp = client.get("/api/v1/file", params={"path": "a.txt"})
    assert resp.status_code == 200
    assert resp.json() == {"content": "content"}


def test_t_rest_file_post_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-FILE-POST-200"""
    monkeypatch.setattr("src.api.rest.write_file", lambda path, content: {"status": "ok"})
    resp = client.post("/api/v1/file", json={"path": "a.txt", "content": "x"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_t_rest_exec_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-EXEC-200"""
    monkeypatch.setattr("src.api.rest.exec_cmd", lambda cmd: "done")
    resp = client.post("/api/v1/exec", json={"cmd": "git status"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "done"}


def test_t_rest_file_get_missing_maps_404(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-FILE-MISSING-404"""

    def fail(path: str) -> str:
        raise OperationError("File not found")

    monkeypatch.setattr("src.api.rest.read_file", fail)
    resp = client.get("/api/v1/file", params={"path": "missing.txt"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "File not found"


def test_t_rest_operation_error_maps_400(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-OP-ERROR-400"""

    def fail(url: str, destination: str | None = None, credential=None, ssh_identity_file=None) -> str:
        raise OperationError("boom")

    monkeypatch.setattr("src.api.rest.clone_repo", fail)
    resp = client.post("/api/v1/clone", json={"url": "https://example/repo.git"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "boom"


def test_t_rest_clone_registers_inventory(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CLONE-INV-REGISTER"""
    captured = {}

    monkeypatch.setattr(
        "src.api.rest.clone_repo",
        lambda url, destination=None, credential=None, ssh_identity_file=None: "cloned",
    )
    monkeypatch.setattr(
        "src.api.rest.resolve_clone_target",
        lambda url, destination=None: "/workspace/repo-manager-copy",
    )

    def fake_register(root_path: str, origin_url: str) -> None:
        captured["root_path"] = root_path
        captured["origin_url"] = origin_url

    monkeypatch.setattr("src.api.rest.inventory_service.register_cloned_repository", fake_register)

    resp = client.post("/api/v1/clone", json={"url": "https://example/repo.git"})
    assert resp.status_code == 200
    assert captured == {
        "root_path": "/workspace/repo-manager-copy",
        "origin_url": "https://example/repo.git",
    }


def test_t_rest_checkout_error_maps_400(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CHECKOUT-OP-ERROR-400"""

    def fail(branch: str) -> str:
        raise OperationError("checkout failed")

    monkeypatch.setattr("src.api.rest.checkout", fail)
    resp = client.post("/api/v1/checkout", json={"branch": "feature"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "checkout failed"


def test_t_rest_commit_error_maps_400(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-COMMIT-OP-ERROR-400"""

    def fail(message: str) -> str:
        raise OperationError("commit failed")

    monkeypatch.setattr("src.api.rest.commit", fail)
    resp = client.post("/api/v1/commit", json={"message": "test"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "commit failed"


def test_t_rest_push_error_maps_400(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-PUSH-OP-ERROR-400"""

    def fail(remote: str, branch: str) -> str:
        raise OperationError("push failed")

    monkeypatch.setattr("src.api.rest.push", fail)
    resp = client.post("/api/v1/push", json={"remote": "origin", "branch": "main"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "push failed"


def test_t_rest_file_post_error_maps_400(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-FILE-WRITE-OP-ERROR-400"""

    def fail(path: str, content: str) -> dict:
        raise OperationError("write failed")

    monkeypatch.setattr("src.api.rest.write_file", fail)
    resp = client.post("/api/v1/file", json={"path": "test.txt", "content": "data"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "write failed"


def test_t_rest_exec_error_maps_400(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-EXEC-OP-ERROR-400"""

    def fail(cmd: str) -> str:
        raise OperationError("exec failed")

    monkeypatch.setattr("src.api.rest.exec_cmd", fail)
    resp = client.post("/api/v1/exec", json={"cmd": "git status"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "exec failed"


def test_t_rest_credential_list_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CREDENTIAL-LIST-200"""
    monkeypatch.setattr(
        "src.api.rest.credential_store.list_credentials",
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
    resp = client.get("/api/v1/credentials")
    assert resp.status_code == 200
    assert resp.json()["credentials"][0]["credential_id"] == "cred-1"
    assert "secret" not in resp.json()["credentials"][0]


def test_t_rest_credential_create_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CREDENTIAL-CREATE-200"""
    monkeypatch.setattr(
        "src.api.rest.credential_store.create_credential",
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
        "/api/v1/credentials",
        json={
            "name": "GitLab PAT",
            "provider": "gitlab",
            "host": "gitlab.com",
            "username": "oauth2",
            "secret": "token-value",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["credential_id"] == "cred-1"
    assert "secret" not in resp.json()


def test_t_rest_credential_revoke_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CREDENTIAL-REVOKE-200"""
    monkeypatch.setattr(
        "src.api.rest.credential_store.revoke_credential",
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
    resp = client.delete("/api/v1/credentials/cred-1")
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_t_rest_credential_drivers_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CREDENTIAL-DRIVERS-200"""
    monkeypatch.setattr("src.api.rest.credential_store.secret_driver_name", "keyring")
    monkeypatch.setattr(
        "src.api.rest.list_secret_drivers",
        lambda: [{"name": "keyring", "is_secure": True}],
    )
    resp = client.get("/api/v1/credentials/drivers")
    assert resp.status_code == 200
    assert resp.json()["active_driver"] == "keyring"
    assert resp.json()["drivers"][0]["name"] == "keyring"


def test_t_rest_ssh_identity_create_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-SSH-IDENTITY-CREATE-200"""
    monkeypatch.setattr(
        "src.api.rest.ssh_identity_store.create_identity",
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
        "/api/v1/ssh-identities",
        json={"name": "GitLab Key", "host": "gitlab.com", "username": "git"},
    )
    assert resp.status_code == 200
    assert resp.json()["identity_id"] == "ssh-1"
    assert "public_key" in resp.json()


def test_t_rest_ssh_identity_list_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-SSH-IDENTITY-LIST-200"""
    monkeypatch.setattr(
        "src.api.rest.ssh_identity_store.list_identities",
        lambda: [
            type(
                "Meta",
                (),
                {
                    "identity_id": "ssh-1",
                    "name": "GitLab Key",
                    "host": "gitlab.com",
                    "username": "git",
                    "identity_file": "C:/keys/ssh-1",
                    "public_key": "ssh-ed25519 AAAAB3Nza...",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                    "revoked_at": None,
                    "is_active": True,
                },
            )()
        ],
    )
    resp = client.get("/api/v1/ssh-identities")
    assert resp.status_code == 200
    assert resp.json()["ssh_identities"][0]["identity_id"] == "ssh-1"


def test_t_rest_credential_update_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CREDENTIAL-UPDATE-200"""
    monkeypatch.setattr(
        "src.api.rest.credential_store.update_credential",
        lambda credential_id, **kwargs: type(
            "Meta",
            (),
            {
                "credential_id": credential_id,
                "name": kwargs["name"],
                "provider": "gitlab",
                "host": "gitlab.com",
                "username": kwargs["username"],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-02T00:00:00Z",
                "revoked_at": None,
                "is_active": True,
            },
        )(),
    )
    resp = client.put(
        "/api/v1/credentials/cred-1",
        json={"name": "Updated PAT", "username": "oauth2"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated PAT"


@pytest.mark.parametrize(
    ("endpoint", "payload"),
    [
        ("/api/v1/clone", {}),
        ("/api/v1/checkout", {}),
        ("/api/v1/commit", {}),
        ("/api/v1/exec", {}),
        ("/api/v1/file", {"path": "a.txt"}),
    ],
)
def test_t_schema_required_fields_422(client, endpoint: str, payload: dict) -> None:
    """T-SCHEMA-REQUIRED-422"""
    resp = client.post(endpoint, json=payload)
    assert resp.status_code == 422
