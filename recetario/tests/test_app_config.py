from unittest.mock import MagicMock, patch

from django.apps import apps
from django.core.cache import cache
from django.test import TestCase, override_settings

from recetario.tasks import precargar_totales_usuarios


class TestRecetarioConfig(TestCase):
    def setUp(self) -> None:
        cache.clear()  # Limpiar cache antes de cada test

    @patch("recetario.tasks.precargar_totales_usuarios")  # Update patch target
    @patch("recetario.apps.cache")
    def test_ready_executes_task_when_cache_empty(
        self, mock_cache: MagicMock, mock_task: MagicMock
    ) -> None:
        # Configurar mocks
        mock_cache.get.return_value = None
        mock_task.delay.return_value = MagicMock()

        # Obtener y ejecutar la configuración de la app
        app_config = apps.get_app_config("recetario")
        app_config.ready()

        # Verificar que se llamó a cache.get
        mock_cache.get.assert_called_once_with("totales_precargados")

        # Verificar que se llamó a la tarea
        mock_task.delay.assert_called_once()

        # Verificar que se actualizó el cache
        mock_cache.set.assert_called_once_with(
            "totales_precargados", True, timeout=3600
        )

    @patch("recetario.tasks.precargar_totales_usuarios")  # Update patch target
    @patch("recetario.apps.cache")
    def test_ready_skips_task_when_cache_exists(
        self, mock_cache: MagicMock, mock_task: MagicMock
    ) -> None:
        # Configurar mock para simular que ya existe el cache
        mock_cache.get.return_value = True

        # Obtener y ejecutar la configuración de la app
        app_config = apps.get_app_config("recetario")
        app_config.ready()

        # Verificar que se verificó el cache
        mock_cache.get.assert_called_once_with("totales_precargados")

        # Verificar que NO se llamó a la tarea
        mock_task.delay.assert_not_called()

        # Verificar que NO se actualizó el cache
        mock_cache.set.assert_not_called()

    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True
    )  # Para ejecutar tareas sincrónicamente
    def test_ready_integration(self) -> None:

        # Mockear la tarea para verificar que se llama
        with patch.object(precargar_totales_usuarios, "delay") as mock_delay:
            app_config = apps.get_app_config("recetario")
            app_config.ready()

            # Verificar que se llamó a la tarea
            mock_delay.assert_called_once()

    @patch("recetario.apps.import_module")
    def test_signals_imported(self, mock_import: MagicMock) -> None:
        # Verificar que se importan las señales
        app_config = apps.get_app_config("recetario")
        app_config.ready()

        # Verificar que se intentó importar las señales
        mock_import.assert_called_with("recetario.signals")
