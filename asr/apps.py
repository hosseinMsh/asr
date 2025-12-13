from django.apps import AppConfig

class AsrConfig(AppConfig):
    default_auto_field='django.db.models.BigAutoField'
    name='asr'

    def ready(self):
        from . import signals  # noqa
