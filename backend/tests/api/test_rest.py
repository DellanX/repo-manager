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
    monkeypatch.setattr("src.api.rest.clone_repo", lambda url, destination=None: "cloned")
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

    def fake_clone(url: str, destination: str | None = None) -> str:
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

    def fail(url: str, destination: str | None = None) -> str:
        raise OperationError("boom")

    monkeypatch.setattr("src.api.rest.clone_repo", fail)
    resp = client.post("/api/v1/clone", json={"url": "https://example/repo.git"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "boom"


def test_t_rest_clone_registers_inventory(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CLONE-INV-REGISTER"""
    captured = {}

    monkeypatch.setattr("src.api.rest.clone_repo", lambda url, destination=None: "cloned")
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
