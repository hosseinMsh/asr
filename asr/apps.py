from django.apps import AppConfig

class AsrConfig(AppConfig):
    default_auto_field='django.db.models.BigAutoField'
    name='asr'

    def ready(self):
        # ensure signal receivers are registered
        from .utils import signals  # noqa: F401
