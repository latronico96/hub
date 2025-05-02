import logging
from importlib import import_module
from typing import Any

from django.apps import AppConfig
from django.core.cache import cache
from django.db import connection
from django.db.models.signals import post_migrate
from django.db.utils import OperationalError, ProgrammingError
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class RecetarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recetario"

    def ready(self) -> None:
        # Importar señales
        import_module("recetario.signals")

        # Registrar el manejador post-migrate
        self._register_post_migrate_handler()

        # Intentar precargar cache al iniciar (si las tablas existen)
        self._try_precache_data()

    def _register_post_migrate_handler(self) -> None:
        """Registra el handler para ejecutarse después de las migraciones."""

        @receiver(post_migrate)
        def on_post_migrate(sender: AppConfig, **kwargs: Any) -> None:
            if sender.name in ["users", "recetario"]:
                self._try_precache_data()

    def _try_precache_data(self, max_retries: int = 3) -> None:
        """Intenta precargar los datos con mecanismo de reintento."""
        if cache.get("totales_precargados"):
            return

        try:
            if self._required_tables_exist():
                from recetario.tasks import (  # noqa: E501  # pylint: disable=import-outside-toplevel
                    precargar_totales_usuarios,
                )

                precargar_totales_usuarios.delay()
                cache.set("totales_precargados", True, timeout=3600)
        except (OperationalError, ProgrammingError) as e:
            logger.warning("Error al verificar tablas: %s. Reintentando...", e)
            if max_retries > 0:
                self._try_precache_data(max_retries - 1)

    def _required_tables_exist(self) -> bool:
        """Verifica si las tablas requeridas existen en la base de datos."""
        required_tables = {
            "users_user",  # Tabla de usuarios
            "recetario_receta",  # Ejemplo: tabla de recetas
        }

        try:
            existing_tables = set(connection.introspection.table_names())
            return required_tables.issubset(existing_tables)
        except (OperationalError, ProgrammingError):
            return False
