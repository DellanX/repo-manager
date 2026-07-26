from __future__ import annotations

import os
import sqlite3
import subprocess
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from src.core import events
from src.core.config import WORKSPACE


class SSHIdentityStoreError(Exception):
    pass


@dataclass(frozen=True)
class SSHIdentityMetadata:
    identity_id: str
    name: str
    host: str
    username: str
    identity_file: str
    public_key: str
    created_at: str
    updated_at: str
    revoked_at: str | None
    is_active: bool


@dataclass(frozen=True)
class SSHIdentityForUse:
    identity_id: str
    host: str
    username: str
    identity_file: str


class SSHIdentityStoreService:
    def __init__(self, db_path: str | None = None, ssh_root: str | None = None) -> None:
        default_root = Path(WORKSPACE) / ".repo-manager"
        db_value = db_path or os.getenv(
            "REPO_MANAGER_SSH_IDENTITY_DB_PATH",
            str(default_root / "ssh-identities.sqlite3"),
        )
        ssh_root_value = ssh_root or os.getenv(
            "REPO_MANAGER_SSH_IDENTITY_ROOT",
            str(default_root / "ssh"),
        )
        self.db_path = Path(db_value)
        self.ssh_root = Path(ssh_root_value)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ssh_root.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ssh_identities (
                    identity_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    host TEXT NOT NULL,
                    username TEXT NOT NULL,
                    identity_file TEXT NOT NULL,
                    public_key TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    revoked_at TEXT
                )
                """
            )
            conn.commit()

    def create_identity(self, name: str, host: str, username: str = "git") -> SSHIdentityMetadata:
        cleaned_name = name.strip()
        cleaned_host = host.strip().lower()
        cleaned_username = username.strip()
        if not cleaned_name:
            raise SSHIdentityStoreError("Identity name is required")
        if not cleaned_host:
            raise SSHIdentityStoreError("Identity host is required")
        if not cleaned_username:
            raise SSHIdentityStoreError("Identity username is required")

        identity_id = f"ssh-{uuid.uuid4().hex}"
        private_key_path = self.ssh_root / identity_id
        public_key_path = self.ssh_root / f"{identity_id}.pub"
        comment = f"{cleaned_name}@{cleaned_host}"

        command = [
            "ssh-keygen",
            "-t",
            "ed25519",
            "-N",
            "",
            "-f",
            str(private_key_path),
            "-C",
            comment,
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            message = result.stderr.strip() or "Failed to generate SSH identity"
            raise SSHIdentityStoreError(message)

        try:
            os.chmod(private_key_path, 0o600)
        except OSError:
            pass

        if not public_key_path.exists():
            raise SSHIdentityStoreError("SSH public key was not generated")
        public_key = public_key_path.read_text(encoding="utf-8").strip()

        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ssh_identities (
                    identity_id, name, host, username, identity_file, public_key,
                    created_at, updated_at, revoked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    identity_id,
                    cleaned_name,
                    cleaned_host,
                    cleaned_username,
                    str(private_key_path),
                    public_key,
                    now,
                    now,
                    None,
                ),
            )
            conn.commit()

        events.operation_events.record(
            "ssh_identity",
            "create",
            "completed",
            {"identity_id": identity_id, "host": cleaned_host},
        )
        return self._get_metadata(identity_id)

    def list_identities(self) -> list[SSHIdentityMetadata]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    identity_id, name, host, username, identity_file, public_key,
                    created_at, updated_at, revoked_at
                FROM ssh_identities
                ORDER BY created_at DESC
                """
            ).fetchall()
        return [self._row_to_metadata(row) for row in rows]

    def revoke_identity(self, identity_id: str) -> SSHIdentityMetadata:
        metadata = self._get_metadata(identity_id)
        if metadata.revoked_at is not None:
            raise SSHIdentityStoreError("SSH identity is already revoked")

        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE ssh_identities
                SET revoked_at = ?, updated_at = ?
                WHERE identity_id = ?
                """,
                (now, now, identity_id),
            )
            conn.commit()

        private_key_path = Path(metadata.identity_file)
        public_key_path = Path(f"{metadata.identity_file}.pub")
        if private_key_path.exists():
            private_key_path.unlink()
        if public_key_path.exists():
            public_key_path.unlink()

        events.operation_events.record(
            "ssh_identity",
            "revoke",
            "completed",
            {"identity_id": identity_id},
        )
        return self._get_metadata(identity_id)

    def get_identity_for_use(self, identity_id: str, url: str) -> SSHIdentityForUse:
        metadata = self._get_metadata(identity_id)
        if not metadata.is_active:
            raise SSHIdentityStoreError("SSH identity is revoked")

        requested_host = self._extract_host(url)
        if not requested_host:
            raise SSHIdentityStoreError("Clone URL must include a host")
        if requested_host.lower() != metadata.host:
            raise SSHIdentityStoreError("SSH identity host does not match clone URL host")

        identity_path = Path(metadata.identity_file)
        if not identity_path.exists():
            raise SSHIdentityStoreError("SSH identity file is unavailable")

        events.operation_events.record(
            "ssh_identity",
            "use",
            "completed",
            {"identity_id": identity_id, "host": metadata.host},
        )
        return SSHIdentityForUse(
            identity_id=metadata.identity_id,
            host=metadata.host,
            username=metadata.username,
            identity_file=metadata.identity_file,
        )

    def _extract_host(self, url: str) -> str:
        parsed = urlsplit(url)
        if parsed.hostname:
            return parsed.hostname
        if "@" in url and ":" in url:
            after_at = url.split("@", 1)[1]
            return after_at.split(":", 1)[0]
        if ":" in url and "://" not in url:
            return url.split(":", 1)[0]
        return ""

    def _get_metadata(self, identity_id: str) -> SSHIdentityMetadata:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    identity_id, name, host, username, identity_file, public_key,
                    created_at, updated_at, revoked_at
                FROM ssh_identities
                WHERE identity_id = ?
                """,
                (identity_id,),
            ).fetchone()
        if row is None:
            raise SSHIdentityStoreError("SSH identity not found")
        return self._row_to_metadata(row)

    def _row_to_metadata(self, row: sqlite3.Row) -> SSHIdentityMetadata:
        revoked_at = row["revoked_at"]
        return SSHIdentityMetadata(
            identity_id=row["identity_id"],
            name=row["name"],
            host=row["host"],
            username=row["username"],
            identity_file=row["identity_file"],
            public_key=row["public_key"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            revoked_at=revoked_at,
            is_active=revoked_at is None,
        )


ssh_identity_store = SSHIdentityStoreService()
