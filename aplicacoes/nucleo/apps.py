from django.apps import AppConfig


class NucleoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'aplicacoes.nucleo'
    verbose_name = 'Núcleo'

    def ready(self):
        import aplicacoes.nucleo.signals  # noqa: F401
        from aplicacoes.nucleo.signals import conectar_signals_webhooks
        conectar_signals_webhooks()
