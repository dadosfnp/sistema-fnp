from django.apps import AppConfig


class EngajamentoConfig(AppConfig):
    default_auto_field = 'django.db.models.UUIDField'
    name = 'aplicacoes.engajamento'
    verbose_name = 'Engajamento'

    def ready(self):
        import aplicacoes.engajamento.signals  # noqa: F401
