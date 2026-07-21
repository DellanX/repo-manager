from pathlib import Path

import pytest

from src.services.file_operations import _resolve_workspace_path, read_file, write_file
from src.services.git_operations import OperationError


def test_t_file_write_and_read_success(temp_workspace: Path) -> None:
    """T-FILE-WRITE-READ-200"""
    result = write_file("nested/hello.txt", "hi")
    assert result == {"status": "ok"}
    assert read_file("nested/hello.txt") == "hi"


def test_t_file_read_missing_raises_operation_error(temp_workspace: Path) -> None:
    """T-FILE-READ-404"""
    with pytest.raises(OperationError, match="File not found"):
        read_file("missing.txt")


def test_t_file_read_traversal_rejected(temp_workspace: Path) -> None:
    """T-FILE-READ-TRAVERSAL-400"""
    with pytest.raises(OperationError, match="Path escapes workspace"):
        _resolve_workspace_path("../outside.txt")


def test_t_file_write_traversal_rejected(temp_workspace: Path) -> None:
    """T-FILE-WRITE-TRAVERSAL-400"""
    with pytest.raises(OperationError, match="Path escapes workspace"):
        write_file("../outside.txt", "x")
