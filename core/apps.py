"""
Este módulo define la configuración de la aplicación 'core' para el proyecto Django.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
