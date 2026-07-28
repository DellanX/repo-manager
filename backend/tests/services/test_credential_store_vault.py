from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest
from src.services.credential_store import CredentialStoreError, VaultKV2SecretDriver


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> _FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_t_vault_backend_set_secret_uses_kv_v2_data_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-CRED-VAULT-SET-PATH"""
    captured = {}

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["timeout"] = timeout
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        return _FakeResponse("{}")

    monkeypatch.setattr("src.services.credential_store.request.urlopen", fake_urlopen)
    backend = VaultKV2SecretDriver(
        addr="https://vault.example",
        token="vault-token",
        mount="secret",
        path_prefix="repo-manager/credentials",
    )
    backend.set_secret("cred-1", "secret-value")

    assert captured["url"] == "https://vault.example/v1/secret/data/repo-manager/credentials/cred-1"
    assert captured["method"] == "POST"
    assert captured["timeout"] == 10
    assert captured["payload"] == {"data": {"secret": "secret-value"}}


def test_t_vault_backend_get_secret_reads_nested_data(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-CRED-VAULT-GET-DATA"""
    body = json.dumps({"data": {"data": {"secret": "secret-value"}}})

    monkeypatch.setattr(
        "src.services.credential_store.request.urlopen",
        lambda req, timeout: _FakeResponse(body),
    )
    backend = VaultKV2SecretDriver(
        addr="https://vault.example",
        token="vault-token",
    )
    assert backend.get_secret("cred-1") == "secret-value"


def test_t_vault_backend_get_secret_404_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """T-CRED-VAULT-GET-404"""

    def fake_urlopen(req, timeout):
        raise HTTPError(req.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr("src.services.credential_store.request.urlopen", fake_urlopen)
    backend = VaultKV2SecretDriver(
        addr="https://vault.example",
        token="vault-token",
    )
    assert backend.get_secret("cred-1") is None


def test_t_vault_backend_requires_addr_and_token() -> None:
    """T-CRED-VAULT-CONFIG-REQUIRED"""
    backend = VaultKV2SecretDriver(addr=None, token=None)
    with pytest.raises(CredentialStoreError, match="REPO_MANAGER_VAULT_ADDR"):
        backend.set_secret("cred-1", "secret-value")
