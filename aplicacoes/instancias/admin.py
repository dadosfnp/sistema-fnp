"""Admin Unfold para Instância (Espaço de Diálogo Federativo) e Representação."""

from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from aplicacoes.documentos.admin import DocumentoGenericInline

from .models import Instancia, Representacao


class RepresentacaoInline(TabularInline):
    """Inline de representações exibido dentro do admin de Instância."""
    model = Representacao
    extra = 0
    fields = ['pessoa', 'funcao', 'tipo_mandato', 'inicio_mandato', 'fim_mandato', 'vigente']
    autocomplete_fields = ['pessoa']


@admin.register(Instancia)
class InstanciaAdmin(ModelAdmin):
    """Admin de Instância com fieldsets agrupando identificação, arcabouço e funcionamento."""
    list_display = ['nome', 'origem', 'forma', 'categoria', 'status', 'periodicidade_reunioes']
    list_filter = ['origem', 'forma', 'categoria', 'status', 'periodicidade_reunioes']
    search_fields = ['nome', 'numero_arcabouco', 'descricao']
    autocomplete_fields = ['instancia_principal', 'ponto_focal_fnp']
    inlines = [RepresentacaoInline, DocumentoGenericInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'origem', 'forma', 'categoria', 'instancia_principal', 'descricao'),
        }),
        ('Arcabouço legal', {
            'fields': ('tipo_arcabouco', 'numero_arcabouco', 'link_arcabouco'),
        }),
        ('Funcionamento', {
            'fields': ('status', 'tempo_mandato', 'periodicidade_reunioes', 'possui_gt_ct', 'composicao'),
        }),
        ('FNP', {
            'fields': ('ponto_focal_fnp', 'link_site'),
        }),
    )


@admin.register(Representacao)
class RepresentacaoAdmin(ModelAdmin):
    """Admin de Representação para gerenciar vínculos individuais a instâncias."""
    list_display = ['pessoa', 'instancia', 'funcao', 'tipo_mandato', 'inicio_mandato', 'fim_mandato', 'vigente']
    list_filter = ['funcao', 'tipo_mandato', 'vigente', 'documento_indicacao']
    search_fields = ['pessoa__nome', 'instancia__nome']
    autocomplete_fields = ['pessoa', 'instancia']
