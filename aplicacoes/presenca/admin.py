"""Admin Unfold para Presença universal + inline genérico reutilizável."""

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from unfold.admin import ModelAdmin

from .models import Presenca


class PresencaGenericInline(GenericTabularInline):
    """Inline genérico de presenças — incluir em qualquer ModelAdmin que precise rastrear quem foi.

    Exemplo: ``inlines = [PresencaGenericInline]`` em ``AtividadeAdmin``.
    """
    model = Presenca
    extra = 0
    fields = ['pessoa', 'status', 'forma', 'municipio', 'observacao']
    autocomplete_fields = ['pessoa', 'municipio']
    ct_field = 'content_type'
    ct_fk_field = 'object_id'


@admin.register(Presenca)
class PresencaAdmin(ModelAdmin):
    """Admin centralizado de Presença, com filtros por status, forma e tipo de entidade."""
    list_display = ['pessoa', 'status', 'forma', 'municipio', 'content_type', 'criado_em']
    list_filter = ['status', 'forma', 'content_type']
    search_fields = ['pessoa__nome', 'observacao']
    autocomplete_fields = ['pessoa', 'municipio']
    readonly_fields = ['registrado_por', 'criado_em', 'atualizado_em']

    def save_model(self, request, obj, form, change):
        """Registra automaticamente o usuário que está marcando a presença."""
        if not obj.registrado_por_id:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)
