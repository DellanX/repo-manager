import pytest

from src.services.git_operations import OperationError


def test_t_rest_health_200(client) -> None:
    """T-REST-HEALTH-200"""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_t_rest_clone_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CLONE-200"""
    monkeypatch.setattr("src.api.rest.clone_repo", lambda url: "cloned")
    resp = client.post("/clone", json={"url": "https://example/repo.git"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "cloned"}


def test_t_rest_checkout_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-CHECKOUT-200"""
    monkeypatch.setattr("src.api.rest.checkout", lambda branch: "ok")
    resp = client.post("/checkout", json={"branch": "main"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "ok"}


def test_t_rest_commit_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-COMMIT-200"""
    monkeypatch.setattr("src.api.rest.commit", lambda message: "ok")
    resp = client.post("/commit", json={"message": "m"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "ok"}


def test_t_rest_push_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-PUSH-200"""
    monkeypatch.setattr("src.api.rest.push", lambda remote, branch: "ok")
    resp = client.post("/push", json={"remote": "origin", "branch": "main"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "ok"}


def test_t_rest_file_get_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-FILE-GET-200"""
    monkeypatch.setattr("src.api.rest.read_file", lambda path: "content")
    resp = client.get("/file", params={"path": "a.txt"})
    assert resp.status_code == 200
    assert resp.json() == {"content": "content"}


def test_t_rest_file_post_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-FILE-POST-200"""
    monkeypatch.setattr("src.api.rest.write_file", lambda path, content: {"status": "ok"})
    resp = client.post("/file", json={"path": "a.txt", "content": "x"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_t_rest_exec_200(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-EXEC-200"""
    monkeypatch.setattr("src.api.rest.exec_cmd", lambda cmd: "done")
    resp = client.post("/exec", json={"cmd": "git status"})
    assert resp.status_code == 200
    assert resp.json() == {"output": "done"}


def test_t_rest_file_get_missing_maps_404(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-FILE-MISSING-404"""

    def fail(path: str) -> str:
        raise OperationError("File not found")

    monkeypatch.setattr("src.api.rest.read_file", fail)
    resp = client.get("/file", params={"path": "missing.txt"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "File not found"


def test_t_rest_operation_error_maps_400(client, monkeypatch: pytest.MonkeyPatch) -> None:
    """T-REST-OP-ERROR-400"""

    def fail(url: str) -> str:
        raise OperationError("boom")

    monkeypatch.setattr("src.api.rest.clone_repo", fail)
    resp = client.post("/clone", json={"url": "https://example/repo.git"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "boom"


@pytest.mark.parametrize(
    ("endpoint", "payload"),
    [
        ("/clone", {}),
        ("/checkout", {}),
        ("/commit", {}),
        ("/exec", {}),
        ("/file", {"path": "a.txt"}),
    ],
)
def test_t_schema_required_fields_422(client, endpoint: str, payload: dict) -> None:
    """T-SCHEMA-REQUIRED-422"""
    resp = client.post(endpoint, json=payload)
    assert resp.status_code == 422
