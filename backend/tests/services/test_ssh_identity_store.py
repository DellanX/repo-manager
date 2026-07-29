from __future__ import annotations

from pathlib import Path

import pytest
from src.services.ssh_identity_store import SSHIdentityStoreError, SSHIdentityStoreService


class _DummyCompleted:
    def __init__(self, returncode: int, stderr: str = "") -> None:
        self.returncode = returncode
        self.stderr = stderr


def test_t_ssh_identity_create_and_use(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """T-SSH-IDENTITY-CREATE-USE"""
    ssh_root = tmp_path / "ssh"

    def fake_run(command, capture_output=True, text=True):
        identity_path = Path(command[6])
        identity_path.parent.mkdir(parents=True, exist_ok=True)
        identity_path.write_text("private", encoding="utf-8")
        Path(f"{identity_path}.pub").write_text(
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest public-key",
            encoding="utf-8",
        )
        return _DummyCompleted(0)

    monkeypatch.setattr("src.services.ssh_identity_store.subprocess.run", fake_run)
    service = SSHIdentityStoreService(
        db_path=str(tmp_path / "ssh-identities.sqlite3"),
        ssh_root=str(ssh_root),
    )

    identity = service.create_identity(name="GitLab Key", host="gitlab.com")
    assert identity.host == "gitlab.com"
    assert identity.public_key.startswith("ssh-ed25519")

    for_use = service.get_identity_for_use(identity.identity_id, "git@gitlab.com:group/repo.git")
    assert for_use.identity_file == identity.identity_file


def test_t_ssh_identity_host_mismatch_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """T-SSH-IDENTITY-HOST-MISMATCH"""
    ssh_root = tmp_path / "ssh"

    def fake_run(command, capture_output=True, text=True):
        identity_path = Path(command[6])
        identity_path.parent.mkdir(parents=True, exist_ok=True)
        identity_path.write_text("private", encoding="utf-8")
        Path(f"{identity_path}.pub").write_text(
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITest public-key",
            encoding="utf-8",
        )
        return _DummyCompleted(0)

    monkeypatch.setattr("src.services.ssh_identity_store.subprocess.run", fake_run)
    service = SSHIdentityStoreService(
        db_path=str(tmp_path / "ssh-identities.sqlite3"),
        ssh_root=str(ssh_root),
    )
    identity = service.create_identity(name="GitHub Key", host="github.com")
    with pytest.raises(SSHIdentityStoreError, match="host does not match"):
        service.get_identity_for_use(identity.identity_id, "git@gitlab.com:group/repo.git")
