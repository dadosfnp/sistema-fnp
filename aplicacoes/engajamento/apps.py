from django.apps import AppConfig


class EngajamentoConfig(AppConfig):
    default_auto_field = 'django.db.models.UUIDField'
    name = 'aplicacoes.engajamento'
    verbose_name = 'Engajamento'

    def ready(self):
        from aplicacoes.engajamento.signals import conectar_signals
        from aplicacoes.engajamento.servicos.calculo import registrar_fontes_default
        registrar_fontes_default()
        conectar_signals()
