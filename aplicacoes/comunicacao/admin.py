"""Admin Unfold para Templates de e-mail e registros de Envio."""

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Envio, TemplateEmail


@admin.register(TemplateEmail)
class TemplateEmailAdmin(ModelAdmin):
    """Admin de TemplateEmail — editores podem criar e ajustar templates por categoria."""
    list_display = ['nome', 'categoria', 'ativo']
    list_filter = ['categoria', 'ativo']
    search_fields = ['nome', 'assunto', 'corpo']
    list_editable = ['ativo']
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'categoria', 'descricao', 'ativo'),
        }),
        ('Conteúdo do e-mail', {
            'fields': ('assunto', 'corpo'),
            'description': 'Placeholders disponíveis: {{ entidade }}, {{ pessoa }}, {{ municipio }}.',
        }),
    )


@admin.register(Envio)
class EnvioAdmin(ModelAdmin):
    """Admin de Envio — somente leitura na prática, serve como log auditável."""
    list_display = ['assunto', 'total_destinatarios', 'status', 'enviado_por', 'criado_em']
    list_filter = ['status', 'content_type', 'criado_em']
    search_fields = ['assunto', 'corpo']
    readonly_fields = [
        'content_type', 'object_id', 'template', 'assunto', 'corpo',
        'destinatarios', 'total_destinatarios', 'status', 'enviado_por',
        'erro', 'criado_em', 'atualizado_em',
    ]
