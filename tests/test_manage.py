import subprocess
import sys

import pytest


def test_manage_help():
    """Testea que manage.py muestra la ayuda sin romperse."""
    result = subprocess.run(
        [sys.executable, "manage.py", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    assert "Type 'manage.py help <subcommand>'" in result.stdout


def test_import_error(monkeypatch):
    """Simula que no se puede importar Django y captura el mensaje de error."""

    original_import = __import__

    def raise_import_error(name, *args, **kwargs):
        if name == "django.core.management":
            raise ImportError("Simulated ImportError")
        return original_import(name, *args, **kwargs)

    # Parcheamos django.core.management para simular un fallo
    monkeypatch.setitem(sys.modules, "django.core.management", None)
    monkeypatch.setattr("builtins.__import__", raise_import_error)

    with pytest.raises(ImportError, match="Couldn't import Django"):
        from manage import main

        main()


def test_invalid_command():
    """Testea que manage.py maneja comandos inválidos correctamente."""
    result = subprocess.run(
        [sys.executable, "manage.py", "invalidcommand"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode != 0
    assert "Unknown command: 'invalidcommand'" in result.stderr


def test_execute_command(monkeypatch):
    """Simula la ejecución exitosa de un comando válido."""

    def mock_execute_from_command_line(argv):
        assert argv == ["manage.py", "check"]

    monkeypatch.setattr(
        "django.core.management.execute_from_command_line",
        mock_execute_from_command_line,
    )

    from manage import main

    main(["manage.py", "check"])
