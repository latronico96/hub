# tests/test_asgi.py

import importlib


def test_asgi_application_import() -> None:
    importlib.import_module("hub.asgi")
