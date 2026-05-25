"""Configuração do admin para User (com Perfil inline), LogAlteracao e fila LGPD."""

from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from unfold.admin import ModelAdmin

from aplicacoes.nucleo.models import (
    AceiteTermo, LogAcessoSensivel, LogAlteracao, Perfil,
    PermissaoEntidade, SolicitacaoExclusao,
)


class PerfilInline(admin.StackedInline):
    """Inline para editar o Perfil de acesso diretamente no formulário do User."""
    model = Perfil
    fk_name = 'usuario'  # Perfil tem 2 FKs para User (usuario + aprovado_por); especificamos qual é o inline
    can_delete = False
    verbose_name_plural = 'Perfil de acesso'


class UserAdmin(BaseUserAdmin):
    """Admin customizado do User com inline de Perfil e coluna de tipo de acesso."""
    inlines = [PerfilInline]
    list_display = ['username', 'get_full_name', 'email', 'get_perfil', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff', 'perfil__tipo']

    @admin.display(description='Perfil')
    def get_perfil(self, obj):
        try:
            return obj.perfil.get_tipo_display()
        except Perfil.DoesNotExist:
            return '—'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(LogAlteracao)
class LogAlteracaoAdmin(ModelAdmin):
    """Admin somente-leitura para visualização dos logs de auditoria."""
    list_display = ['data', 'usuario', 'acao', 'modelo', 'objeto_repr']
    list_filter = ['acao', 'modelo', 'data']
    search_fields = ['objeto_repr', 'usuario__username']
    readonly_fields = ['usuario', 'acao', 'modelo', 'objeto_id', 'objeto_repr', 'campos_alterados', 'data']
    date_hierarchy = 'data'

    def has_add_permission(self, request):
        """Logs são criados apenas programaticamente."""
        return False

    def has_change_permission(self, request, obj=None):
        """Logs são imutáveis — edição desabilitada."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Apenas superusuários podem excluir logs."""
        return request.user.is_superuser


@admin.register(Perfil)
class PerfilAdmin(ModelAdmin):
    """Admin do Perfil — fila de aprovação LGPD, escopo e expiração.

    Aqui o DPO/admin libera externos: filtra status_aprovacao=PENDENTE,
    abre o perfil, escolhe tipo + municipios_visiveis + permissões + 2FA
    e usa a ação "Aprovar acesso" para liberar.
    """

    list_display = [
        'usuario_email', 'tipo', 'status_aprovacao_badge',
        'municipio_vinculado', 'expira_em', 'requer_2fa', 'aprovado_em',
    ]
    list_filter = ['status_aprovacao', 'tipo', 'requer_2fa', 'expira_em']
    search_fields = ['usuario__username', 'usuario__email', 'usuario__first_name', 'usuario__last_name']
    filter_horizontal = ['municipios_visiveis']
    raw_id_fields = ['usuario', 'municipio_vinculado', 'aprovado_por']
    actions = ['aprovar_acesso', 'bloquear_acesso', 'estender_90_dias']
    fieldsets = (
        ('Usuário', {'fields': ('usuario', 'tipo')}),
        ('Aprovação (LGPD)', {
            'fields': (
                'status_aprovacao', 'aprovado_por', 'aprovado_em',
                'expira_em', 'justificativa_acesso', 'requer_2fa',
            ),
        }),
        ('Escopo de acesso', {
            'fields': ('municipio_vinculado', 'municipios_visiveis', 'permissoes_extras'),
        }),
    )
    readonly_fields = ['aprovado_em']

    @admin.display(description='Usuário (e-mail)')
    def usuario_email(self, obj):
        return obj.usuario.email or obj.usuario.username

    @admin.display(description='Status', ordering='status_aprovacao')
    def status_aprovacao_badge(self, obj):
        from django.utils.html import format_html
        cores = {
            'pendente': '#f59e0b', 'aprovado': '#10b981',
            'bloqueado': '#ef4444', 'expirado': '#6b7280',
        }
        cor = cores.get(obj.status_aprovacao, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:8px;font-size:11px">{}</span>',
            cor, obj.get_status_aprovacao_display(),
        )

    @admin.action(description='Aprovar acesso dos perfis selecionados')
    def aprovar_acesso(self, request, queryset):
        atualizados = queryset.update(
            status_aprovacao=Perfil.StatusAprovacao.APROVADO,
            aprovado_por=request.user,
            aprovado_em=timezone.now(),
        )
        messages.success(request, f'{atualizados} perfis aprovados.')

    @admin.action(description='Bloquear acesso dos perfis selecionados')
    def bloquear_acesso(self, request, queryset):
        atualizados = queryset.update(status_aprovacao=Perfil.StatusAprovacao.BLOQUEADO)
        messages.warning(request, f'{atualizados} perfis bloqueados.')

    @admin.action(description='Estender validade por +90 dias')
    def estender_90_dias(self, request, queryset):
        from datetime import timedelta
        atualizados = 0
        for p in queryset:
            base = p.expira_em or timezone.now().date()
            p.expira_em = base + timedelta(days=90)
            if p.status_aprovacao == Perfil.StatusAprovacao.EXPIRADO:
                p.status_aprovacao = Perfil.StatusAprovacao.APROVADO
            p.save(update_fields=['expira_em', 'status_aprovacao'])
            atualizados += 1
        messages.success(request, f'{atualizados} perfis estendidos por +90 dias.')


@admin.register(PermissaoEntidade)
class PermissaoEntidadeAdmin(ModelAdmin):
    """ACL por objeto — quem vê qual entidade específica."""
    list_display = ['perfil', 'content_type', 'object_id', 'nivel', 'expira_em', 'concedido_por']
    list_filter = ['nivel', 'content_type', 'expira_em']
    search_fields = ['perfil__usuario__email', 'object_id']
    raw_id_fields = ['perfil', 'concedido_por']
    readonly_fields = ['concedido_em']


@admin.register(LogAcessoSensivel)
class LogAcessoSensivelAdmin(ModelAdmin):
    """Auditoria de LEITURA de dados sensíveis — somente leitura."""
    list_display = ['data', 'usuario', 'modelo', 'objeto_id', 'ip', 'contexto']
    list_filter = ['modelo', 'data', 'contexto']
    search_fields = ['usuario__username', 'usuario__email', 'objeto_id', 'ip']
    readonly_fields = ['usuario', 'modelo', 'objeto_id', 'ip', 'user_agent', 'contexto', 'data']
    date_hierarchy = 'data'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AceiteTermo)
class AceiteTermoAdmin(ModelAdmin):
    list_display = ['usuario', 'versao', 'ip', 'aceito_em']
    list_filter = ['versao', 'aceito_em']
    search_fields = ['usuario__username', 'usuario__email']
    readonly_fields = ['usuario', 'versao', 'ip', 'user_agent', 'aceito_em']

    def has_add_permission(self, request):
        return False


@admin.register(SolicitacaoExclusao)
class SolicitacaoExclusaoAdmin(ModelAdmin):
    """Fila de pedidos LGPD Art. 18 VI — DPO atende manualmente."""
    list_display = ['email_contato', 'status', 'criado_em', 'atendido_em']
    list_filter = ['status', 'criado_em']
    search_fields = ['email_contato', 'usuario__username']
    readonly_fields = ['usuario', 'email_contato', 'motivo', 'criado_em']
    fieldsets = (
        ('Pedido', {'fields': ('usuario', 'email_contato', 'motivo', 'criado_em')}),
        ('Atendimento', {'fields': ('status', 'resposta_dpo', 'atendido_em')}),
    )
