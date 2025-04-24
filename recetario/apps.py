from django.apps import AppConfig


class RecetarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recetario"

    def ready(self) -> None:
        # pylint: disable=import-outside-toplevel,unused-import
        import recetario.signals  # noqa: F401
