"""Admin Unfold para Atividades (reuniões de Instâncias)."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from aplicacoes.documentos.admin import DocumentoGenericInline
from aplicacoes.presenca.admin import PresencaGenericInline

from .models import Atividade


@admin.register(Atividade)
class AtividadeAdmin(ModelAdmin):
    """Admin de Atividade com fieldsets de identificação, agenda e documentação."""
    list_display = [
        'instancia',
        'data_reuniao',
        'tipo_calendario',
        'formato',
        'status',
        'possui_pauta',
        'possui_ata',
        'possui_lista_presenca',
    ]
    list_filter = ['tipo_calendario', 'formato', 'status', 'data_reuniao']
    search_fields = ['titulo', 'instancia__nome', 'pauta_resumo', 'ata_resumo']
    autocomplete_fields = ['instancia']
    date_hierarchy = 'data_reuniao'
    inlines = [DocumentoGenericInline, PresencaGenericInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('instancia', 'titulo', 'tipo_calendario', 'status'),
        }),
        ('Agenda', {
            'fields': ('data_reuniao', 'horario', 'formato', 'local'),
        }),
        ('Conteúdo', {
            'fields': ('pauta_resumo', 'ata_resumo'),
        }),
        ('Documentos vinculados', {
            'fields': ('possui_pauta', 'possui_ata', 'possui_lista_presenca'),
            'description': 'Indique quais documentos já estão no repositório. Os arquivos serão anexados no módulo de documentos (Fase 3).',
        }),
    )
