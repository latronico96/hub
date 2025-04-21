def test_import_wsgi():
    import hub.wsgi

    assert hasattr(hub.wsgi, "application")
