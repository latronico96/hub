from django.apps import apps


def test_core_app_is_registered() -> None:
    assert apps.is_installed("core")
    assert "core" in [app.name for app in apps.get_app_configs()]
