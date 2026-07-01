from django.apps import AppConfig


class EventosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "eventos"
    verbose_name = "Eventos comerciais"

    def ready(self):
        from eventos import receivers  # noqa: F401
