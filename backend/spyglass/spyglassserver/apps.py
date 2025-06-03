from django.apps import AppConfig


class SpyglassserverConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'spyglassserver'

    def ready(self):
        """Import and initialize app modules on startup"""
        import spyglassserver.apps.common  # noqa
