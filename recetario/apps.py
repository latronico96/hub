from django.apps import AppConfig


class RecetarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "recetario"

    def ready(self):
        import recetario.signals
