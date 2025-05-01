from importlib import import_module

from django.apps import AppConfig
from django.core.cache import cache


class RecetarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recetario"

    def ready(self) -> None:
        # pylint: disable=import-outside-toplevel,unused-import
        import_module("recetario.signals")

        if cache.get("totales_precargados") is None:
            from recetario.tasks import precargar_totales_usuarios

            precargar_totales_usuarios.delay()
            cache.set("totales_precargados", True, timeout=3600)
