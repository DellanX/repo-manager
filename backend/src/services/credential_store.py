from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib import request
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit

import keyring
from keyring.errors import KeyringError, NoKeyringError, PasswordDeleteError

from src.core import events
from src.core.config import WORKSPACE

_KEYRING_SERVICE = "repo-manager.credentials"


class CredentialStoreError(Exception):
    pass


@dataclass(frozen=True)
class CredentialMetadata:
    credential_id: str
    name: str
    provider: str
    host: str
    username: str
    created_at: str
    updated_at: str
    revoked_at: str | None
    is_active: bool


@dataclass(frozen=True)
class CredentialForUse:
    credential_id: str
    provider: str
    host: str
    username: str
    secret: str


class SecretBackend:
    def set_secret(self, credential_id: str, secret: str) -> None:
        raise NotImplementedError

    def get_secret(self, credential_id: str) -> str | None:
        raise NotImplementedError

    def delete_secret(self, credential_id: str) -> None:
        raise NotImplementedError


class KeyringSecretBackend(SecretBackend):
    def set_secret(self, credential_id: str, secret: str) -> None:
        try:
            keyring.set_password(_KEYRING_SERVICE, credential_id, secret)
        except NoKeyringError as exc:
            raise CredentialStoreError("No secure keyring backend is available") from exc
        except KeyringError as exc:
            raise CredentialStoreError("Failed to store credential secret securely") from exc

    def get_secret(self, credential_id: str) -> str | None:
        try:
            return keyring.get_password(_KEYRING_SERVICE, credential_id)
        except NoKeyringError as exc:
            raise CredentialStoreError("No secure keyring backend is available") from exc
        except KeyringError as exc:
            raise CredentialStoreError("Failed to access secure credential secret") from exc

    def delete_secret(self, credential_id: str) -> None:
        try:
            keyring.delete_password(_KEYRING_SERVICE, credential_id)
        except PasswordDeleteError as exc:
            raise CredentialStoreError("Credential secret was not found in secure storage") from exc
        except NoKeyringError as exc:
            raise CredentialStoreError("No secure keyring backend is available") from exc
        except KeyringError as exc:
            raise CredentialStoreError("Failed to delete credential secret from secure storage") from exc


class VaultSecretBackend(SecretBackend):
    def __init__(
        self,
        *,
        addr: str | None,
        token: str | None,
        mount: str = "secret",
        path_prefix: str = "repo-manager/credentials",
        namespace: str | None = None,
        timeout_seconds: int = 10,
    ) -> None:
        self.addr = (addr or "").rstrip("/")
        self.token = token or ""
        self.mount = mount.strip("/")
        self.path_prefix = path_prefix.strip("/")
        self.namespace = namespace
        self.timeout_seconds = timeout_seconds

    def _validate_config(self) -> None:
        if not self.addr:
            raise CredentialStoreError("Vault backend requires REPO_MANAGER_VAULT_ADDR")
        if not self.token:
            raise CredentialStoreError("Vault backend requires REPO_MANAGER_VAULT_TOKEN")
        if not self.mount:
            raise CredentialStoreError("Vault backend requires a non-empty mount path")
        if not self.path_prefix:
            raise CredentialStoreError("Vault backend requires a non-empty path prefix")

    def _secret_path(self, credential_id: str) -> str:
        return f"{self.path_prefix}/{credential_id}"

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, object] | None = None,
    ) -> dict[str, object] | None:
        self._validate_config()
        headers = {
            "X-Vault-Token": self.token,
            "Content-Type": "application/json",
        }
        if self.namespace:
            headers["X-Vault-Namespace"] = self.namespace

        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(
            url=f"{self.addr}{path}",
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise CredentialStoreError("Vault response was not a JSON object")
                return parsed
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise CredentialStoreError(f"Vault request failed with HTTP {exc.code}") from exc
        except URLError as exc:
            raise CredentialStoreError("Vault backend is unreachable") from exc
        except json.JSONDecodeError as exc:
            raise CredentialStoreError("Vault returned invalid JSON") from exc

    def set_secret(self, credential_id: str, secret: str) -> None:
        path = self._secret_path(credential_id)
        self._request(
            "POST",
            f"/v1/{self.mount}/data/{path}",
            {"data": {"secret": secret}},
        )

    def get_secret(self, credential_id: str) -> str | None:
        path = self._secret_path(credential_id)
        payload = self._request("GET", f"/v1/{self.mount}/data/{path}")
        if payload is None:
            return None
        data = payload.get("data")
        if not isinstance(data, dict):
            raise CredentialStoreError("Vault response missing data object")
        secret_data = data.get("data")
        if not isinstance(secret_data, dict):
            raise CredentialStoreError("Vault response missing nested secret data")
        secret = secret_data.get("secret")
        if secret is None:
            return None
        if not isinstance(secret, str):
            raise CredentialStoreError("Vault secret value must be a string")
        return secret

    def delete_secret(self, credential_id: str) -> None:
        path = self._secret_path(credential_id)
        payload = self._request("DELETE", f"/v1/{self.mount}/metadata/{path}")
        if payload is None:
            raise CredentialStoreError("Credential secret was not found in secure storage")


def create_secret_backend_from_env() -> SecretBackend:
    backend_name = os.getenv("REPO_MANAGER_SECRET_BACKEND", "keyring").strip().lower()
    if backend_name == "keyring":
        return KeyringSecretBackend()
    if backend_name == "vault":
        return VaultSecretBackend(
            addr=os.getenv("REPO_MANAGER_VAULT_ADDR"),
            token=os.getenv("REPO_MANAGER_VAULT_TOKEN"),
            mount=os.getenv("REPO_MANAGER_VAULT_MOUNT", "secret"),
            path_prefix=os.getenv("REPO_MANAGER_VAULT_PATH_PREFIX", "repo-manager/credentials"),
            namespace=os.getenv("REPO_MANAGER_VAULT_NAMESPACE"),
        )
    raise CredentialStoreError("Unsupported secret backend")


class CredentialStoreService:
    def __init__(
        self,
        db_path: str | None = None,
        secret_backend: SecretBackend | None = None,
    ) -> None:
        default_path = Path(WORKSPACE) / ".repo-manager" / "credentials.sqlite3"
        db_value = db_path or os.getenv("REPO_MANAGER_CREDENTIAL_DB_PATH", str(default_path))
        self.db_path = Path(db_value)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._secret_backend = secret_backend or create_secret_backend_from_env()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS credentials (
                    credential_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    host TEXT NOT NULL,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    revoked_at TEXT
                )
                """
            )
            conn.commit()

    def create_credential(
        self,
        name: str,
        provider: str,
        host: str,
        username: str,
        secret: str,
    ) -> CredentialMetadata:
        cleaned_name = name.strip()
        cleaned_provider = provider.strip().lower()
        cleaned_host = host.strip().lower()
        cleaned_username = username.strip()
        cleaned_secret = secret.strip()

        if not cleaned_name:
            raise CredentialStoreError("Credential name is required")
        if cleaned_provider not in {"github", "gitlab", "azure_devops", "generic"}:
            raise CredentialStoreError("Unsupported credential provider")
        if not cleaned_host:
            raise CredentialStoreError("Credential host is required")
        if not cleaned_username:
            raise CredentialStoreError("Credential username is required")
        if not cleaned_secret:
            raise CredentialStoreError("Credential secret is required")

        now = datetime.now(UTC).isoformat()
        credential_id = f"cred-{uuid.uuid4().hex}"
        metadata = CredentialMetadata(
            credential_id=credential_id,
            name=cleaned_name,
            provider=cleaned_provider,
            host=cleaned_host,
            username=cleaned_username,
            created_at=now,
            updated_at=now,
            revoked_at=None,
            is_active=True,
        )
        self._set_secret(metadata.credential_id, cleaned_secret)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO credentials (
                    credential_id, name, provider, host, username, created_at, updated_at, revoked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata.credential_id,
                    metadata.name,
                    metadata.provider,
                    metadata.host,
                    metadata.username,
                    metadata.created_at,
                    metadata.updated_at,
                    metadata.revoked_at,
                ),
            )
            conn.commit()
        events.operation_events.record(
            "credentials",
            "create",
            "completed",
            {"credential_id": metadata.credential_id, "provider": metadata.provider, "host": metadata.host},
        )
        return metadata

    def list_credentials(self) -> list[CredentialMetadata]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    credential_id, name, provider, host, username,
                    created_at, updated_at, revoked_at
                FROM credentials
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [self._row_to_metadata(row) for row in rows]

    def update_credential(
        self,
        credential_id: str,
        *,
        name: str | None = None,
        host: str | None = None,
        username: str | None = None,
        secret: str | None = None,
    ) -> CredentialMetadata:
        current = self._get_metadata(credential_id)
        if not current.is_active:
            raise CredentialStoreError("Credential is revoked")

        next_name = current.name if name is None else name.strip()
        next_host = current.host if host is None else host.strip().lower()
        next_username = current.username if username is None else username.strip()
        if not next_name:
            raise CredentialStoreError("Credential name is required")
        if not next_host:
            raise CredentialStoreError("Credential host is required")
        if not next_username:
            raise CredentialStoreError("Credential username is required")

        now = datetime.now(UTC).isoformat()
        if secret is not None:
            cleaned_secret = secret.strip()
            if not cleaned_secret:
                raise CredentialStoreError("Credential secret is required")
            self._set_secret(credential_id, cleaned_secret)

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE credentials
                SET name = ?, host = ?, username = ?, updated_at = ?
                WHERE credential_id = ?
                """,
                (next_name, next_host, next_username, now, credential_id),
            )
            conn.commit()
        events.operation_events.record(
            "credentials",
            "update",
            "completed",
            {"credential_id": credential_id, "host": next_host},
        )
        return self._get_metadata(credential_id)

    def revoke_credential(self, credential_id: str) -> CredentialMetadata:
        metadata = self._get_metadata(credential_id)
        if metadata.revoked_at is not None:
            raise CredentialStoreError("Credential is already revoked")

        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE credentials
                SET revoked_at = ?, updated_at = ?
                WHERE credential_id = ?
                """,
                (now, now, credential_id),
            )
            conn.commit()
        self._delete_secret(credential_id)
        events.operation_events.record(
            "credentials",
            "revoke",
            "completed",
            {"credential_id": credential_id},
        )
        return self._get_metadata(credential_id)

    def get_credential_for_use(self, credential_id: str, url: str) -> CredentialForUse:
        metadata = self._get_metadata(credential_id)
        if not metadata.is_active:
            raise CredentialStoreError("Credential is revoked")

        requested_host = (urlsplit(url).hostname or "").lower()
        if not requested_host:
            raise CredentialStoreError("Clone URL must include a host")
        if requested_host != metadata.host:
            raise CredentialStoreError("Credential host does not match clone URL host")

        secret = self._get_secret(credential_id)
        if secret is None:
            raise CredentialStoreError("Credential secret is unavailable")

        events.operation_events.record(
            "credentials",
            "use",
            "completed",
            {"credential_id": credential_id, "host": metadata.host},
        )
        return CredentialForUse(
            credential_id=metadata.credential_id,
            provider=metadata.provider,
            host=metadata.host,
            username=metadata.username,
            secret=secret,
        )

    def _get_metadata(self, credential_id: str) -> CredentialMetadata:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    credential_id, name, provider, host, username,
                    created_at, updated_at, revoked_at
                FROM credentials
                WHERE credential_id = ?
                """,
                (credential_id,),
            ).fetchone()
        if row is None:
            raise CredentialStoreError("Credential not found")
        return self._row_to_metadata(row)

    def _row_to_metadata(self, row: sqlite3.Row) -> CredentialMetadata:
        revoked_at = row["revoked_at"]
        return CredentialMetadata(
            credential_id=row["credential_id"],
            name=row["name"],
            provider=row["provider"],
            host=row["host"],
            username=row["username"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            revoked_at=revoked_at,
            is_active=revoked_at is None,
        )

    def _set_secret(self, credential_id: str, secret: str) -> None:
        self._secret_backend.set_secret(credential_id, secret)

    def _get_secret(self, credential_id: str) -> str | None:
        return self._secret_backend.get_secret(credential_id)

    def _delete_secret(self, credential_id: str) -> None:
        self._secret_backend.delete_secret(credential_id)


credential_store = CredentialStoreService()
