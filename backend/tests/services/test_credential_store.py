from __future__ import annotations

from pathlib import Path

import pytest
from src.services import credential_store
from src.services.credential_store import CredentialStoreError, CredentialStoreService


@pytest.fixture()
def service(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CredentialStoreService:
    secrets: dict[tuple[str, str], str] = {}

    def fake_set_password(service_name: str, username: str, password: str) -> None:
        secrets[(service_name, username)] = password

    def fake_get_password(service_name: str, username: str) -> str | None:
        return secrets.get((service_name, username))

    def fake_delete_password(service_name: str, username: str) -> None:
        key = (service_name, username)
        if key not in secrets:
            raise credential_store.PasswordDeleteError()
        del secrets[key]

    monkeypatch.setattr(credential_store.keyring, "set_password", fake_set_password)
    monkeypatch.setattr(credential_store.keyring, "get_password", fake_get_password)
    monkeypatch.setattr(credential_store.keyring, "delete_password", fake_delete_password)
    return CredentialStoreService(db_path=str(tmp_path / "credentials.sqlite3"))


def test_t_credentials_create_and_list_metadata_only(service: CredentialStoreService) -> None:
    """T-CRED-CREATE-LIST"""
    created = service.create_credential(
        name="GitLab PAT",
        provider="gitlab",
        host="gitlab.com",
        username="oauth2",
        secret="token-value",
    )

    items = service.list_credentials()
    assert len(items) == 1
    assert items[0].credential_id == created.credential_id
    assert items[0].name == "GitLab PAT"
    assert items[0].provider == "gitlab"
    assert not hasattr(items[0], "secret")


def test_t_credentials_get_for_use_host_match_required(service: CredentialStoreService) -> None:
    """T-CRED-USE-HOST-MATCH"""
    created = service.create_credential(
        name="Azure PAT",
        provider="azure_devops",
        host="dev.azure.com",
        username="pat",
        secret="token-value",
    )

    resolved = service.get_credential_for_use(created.credential_id, "https://dev.azure.com/org/project/_git/repo")
    assert resolved.secret == "token-value"

    with pytest.raises(CredentialStoreError, match="host does not match"):
        service.get_credential_for_use(created.credential_id, "https://gitlab.com/group/repo.git")


def test_t_credentials_revoke_blocks_future_use(service: CredentialStoreService) -> None:
    """T-CRED-REVOKE-BLOCKS-USE"""
    created = service.create_credential(
        name="GitHub PAT",
        provider="github",
        host="github.com",
        username="x-access-token",
        secret="token-value",
    )

    revoked = service.revoke_credential(created.credential_id)
    assert revoked.is_active is False

    with pytest.raises(CredentialStoreError, match="revoked"):
        service.get_credential_for_use(created.credential_id, "https://github.com/org/repo.git")


def test_t_credentials_update_rotates_secret(service: CredentialStoreService) -> None:
    """T-CRED-UPDATE-ROTATE"""
    created = service.create_credential(
        name="GitLab PAT",
        provider="gitlab",
        host="gitlab.com",
        username="oauth2",
        secret="old-token",
    )

    updated = service.update_credential(created.credential_id, name="GitLab PAT 2", secret="new-token")
    assert updated.name == "GitLab PAT 2"
    resolved = service.get_credential_for_use(created.credential_id, "https://gitlab.com/group/repo.git")
    assert resolved.secret == "new-token"
