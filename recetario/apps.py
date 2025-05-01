from django.apps import AppConfig
from django.core.cache import cache


class RecetarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recetario"

    def ready(self) -> None:
        # pylint: disable=import-outside-toplevel,unused-import
        import recetario.signals  # noqa: F401

        from .tasks import precargar_totales_usuarios

        if cache.get("totales_precargados") is None:
            precargar_totales_usuarios.delay()
            cache.set("totales_precargados", True, timeout=3600)
