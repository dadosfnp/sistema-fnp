"""Configuração do admin para ConfiguracaoEngajamento (singleton) e Engajamento."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import ConfiguracaoEngajamento, Engajamento


@admin.register(ConfiguracaoEngajamento)
class ConfiguracaoEngajamentoAdmin(ModelAdmin):
    """Admin singleton — permite no máximo um registro de configuração."""
    list_display = ['bienio_atual', 'meta_bienio', 'fator_decaimento', 'penalidade_inadimplente']
    fieldsets = (
        ('Biênio', {
            'fields': ('bienio_atual', 'meta_bienio'),
        }),
        ('Decaimento e penalidades', {
            'fields': ('fator_decaimento', 'penalidade_inadimplente', 'penalidade_parcial'),
        }),
    )

    def has_add_permission(self, request):
        """Permite criar apenas se não existir configuração."""
        return not ConfiguracaoEngajamento.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Configuração não pode ser excluída pelo admin."""
        return False


@admin.register(Engajamento)
class EngajamentoAdmin(ModelAdmin):
    """Admin de Engajamento — campos calculados são somente-leitura."""
    list_display = [
        'municipio', 'bienio', 'pontuacao_normalizada', 'pontuacao_bruta',
        'penalidade_adimplencia', 'total_participacoes', 'nivel',
    ]
    list_filter = ['nivel', 'bienio']
    search_fields = ['municipio__nome']
    readonly_fields = [
        'pontuacao_bruta', 'pontuacao_ano_atual', 'pontuacao_ano_anterior',
        'penalidade_adimplencia', 'pontuacao_normalizada',
        'total_participacoes', 'nivel', 'ultima_atualizacao',
    ]
    autocomplete_fields = ['municipio']
