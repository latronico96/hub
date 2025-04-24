"""Test suite for manage.py functionality."""

import importlib
import subprocess
import sys
from typing import Any, List, cast

import pytest
from _pytest.monkeypatch import MonkeyPatch


def test_manage_help() -> None:
    """Test that manage.py shows help without crashing."""
    result = subprocess.run(
        [sys.executable, "manage.py", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )

    assert result.returncode == 0
    assert "Type 'manage.py help <subcommand>'" in result.stdout


def test_import_error(monkeypatch: MonkeyPatch) -> None:
    """Simulate Django import failure and capture error message."""

    original_import = __import__

    def raise_import_error(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "django.core.management":
            raise ImportError("Simulated ImportError")
        return original_import(name, *args, **kwargs)

    monkeypatch.setitem(sys.modules, "django.core.management", None)
    monkeypatch.setattr("builtins.__import__", raise_import_error)

    with pytest.raises(ImportError, match="Couldn't import Django"):
        # Dynamic import to avoid early failures
        importlib.import_module("manage").main()


def test_invalid_command() -> None:
    """Test manage.py handles invalid commands correctly."""
    result = subprocess.run(
        [sys.executable, "manage.py", "invalidcommand"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    assert result.returncode != 0
    assert "Unknown command: 'invalidcommand'" in result.stderr


def test_execute_command(monkeypatch: MonkeyPatch) -> None:
    """Simulate successful execution of a valid command."""

    def mock_execute_from_command_line(argv: List[str]) -> None:
        assert argv == ["manage.py", "check"]

    # Type-safe monkeypatch
    execute_mock = cast(Any, mock_execute_from_command_line)
    monkeypatch.setattr(
        "django.core.management.execute_from_command_line",
        execute_mock,
    )

    # Isolated import to avoid side effects
    from manage import main  # pylint: disable=import-outside-toplevel

    main(["manage.py", "check"])
