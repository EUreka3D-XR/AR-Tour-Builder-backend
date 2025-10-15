from django.apps import AppConfig

class EurekaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'eureka'

    def ready(self):
        # Import signals so they are connected when the app is ready.
        from . import signals