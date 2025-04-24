def test_import_wsgi() -> None:
    import hub.wsgi

    assert hasattr(hub.wsgi, "application")
