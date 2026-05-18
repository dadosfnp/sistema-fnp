"""Models base do núcleo: ModeloBase (UUID + timestamps), Perfil de acesso e LogAlteracao."""

import uuid

from django.conf import settings
from django.db import models


class AtivosManager(models.Manager):
    """Manager que filtra registros arquivados (soft-deleted).

    Use ``Modelo.ativos.all()`` quando quiser apenas não-arquivados.
    O default ``Modelo.objects`` continua mostrando tudo para compatibilidade
    com queries antigas — sem isso, ``related_name`` e filtros existentes
    deixariam de enxergar dados.
    """

    def get_queryset(self):
        return super().get_queryset().filter(arquivado_em__isnull=True)


class ModeloBase(models.Model):
    """Modelo abstrato com UUID como PK, timestamps e soft delete opt-in."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    criado_em = models.DateTimeField('criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('atualizado em', auto_now=True)
    arquivado_em = models.DateTimeField(
        'arquivado em',
        null=True, blank=True,
        help_text='Marca de soft delete. Use arquivar() para esconder sem perder histórico.',
    )

    objects = models.Manager()
    ativos = AtivosManager()

    class Meta:
        abstract = True

    def arquivar(self, usuario=None):
        """Soft delete reversível — marca como arquivado e loga.

        Args:
            usuario: User que executou (opcional, mas recomendado).
        """
        from django.utils import timezone
        self.arquivado_em = timezone.now()
        self.save(update_fields=['arquivado_em', 'atualizado_em'])
        if usuario is not None:
            from aplicacoes.nucleo.servicos.auditoria import registrar_exclusao
            registrar_exclusao(usuario, self)

    def desarquivar(self):
        """Reverte soft delete."""
        self.arquivado_em = None
        self.save(update_fields=['arquivado_em', 'atualizado_em'])

    @property
    def arquivado(self):
        return self.arquivado_em is not None


class Perfil(models.Model):
    """Perfil de acesso vinculado 1:1 ao User Django.

    Combina:
    - ``tipo``: papel principal (visualizador, editor, admin) — mantido para
      retrocompatibilidade e como atalho para granular.
    - ``permissoes_extras``: lista de strings com permissões granulares
      adicionais (ex: ``pode_importar_ibge``, ``pode_editar_pesos``,
      ``pode_ver_dados_lgpd``). Permite escalar autorização sem migration.
    """

    # Permissoes conhecidas — usadas no admin (autocomplete) e validadas.
    PERMISSOES_DISPONIVEIS = [
        ('pode_editar', 'Editar dados (CRUD básico)'),
        ('pode_importar_ibge', 'Importar municípios do IBGE'),
        ('pode_editar_pesos', 'Editar pesos do engajamento'),
        ('pode_ver_dados_lgpd', 'Ver dados sensíveis (CPF, e-mail, telefone)'),
        ('pode_enviar_email_massa', 'Enviar mala direta'),
        ('pode_exportar', 'Exportar dados (CSV/Excel)'),
        ('pode_arquivar', 'Arquivar registros (soft delete)'),
    ]

    class TipoPerfil(models.TextChoices):
        VISUALIZADOR = 'visualizador', 'Visualizador'
        EDITOR = 'editor', 'Editor'
        ADMIN = 'admin', 'Administrador'

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name='usuario',
    )
    tipo = models.CharField(
        'tipo de perfil',
        max_length=15,
        choices=TipoPerfil.choices,
        default=TipoPerfil.VISUALIZADOR,
    )
    permissoes_extras = models.JSONField(
        'permissões extras',
        default=list,
        blank=True,
        help_text='Lista de slugs de permissão (ex: ["pode_importar_ibge", "pode_exportar"]).',
    )

    class Meta:
        verbose_name = 'perfil'
        verbose_name_plural = 'perfis'

    def __str__(self):
        return f'{self.usuario.get_full_name() or self.usuario.username} — {self.get_tipo_display()}'

    @property
    def eh_editor(self):
        """Retorna True se o perfil possui permissão de edição (tipo ou extra)."""
        if self.tipo in (self.TipoPerfil.EDITOR, self.TipoPerfil.ADMIN):
            return True
        return 'pode_editar' in (self.permissoes_extras or [])

    def pode(self, permissao):
        """Verifica se o perfil tem uma permissão granular específica.

        Admin sempre pode tudo. Editor herda permissões básicas de edição.
        """
        if self.tipo == self.TipoPerfil.ADMIN:
            return True
        if self.tipo == self.TipoPerfil.EDITOR and permissao in {
            'pode_editar', 'pode_exportar', 'pode_arquivar',
        }:
            return True
        return permissao in (self.permissoes_extras or [])


class FiltroSalvo(models.Model):
    """Atalho de filtros que o usuário salvou para reusar em uma lista.

    O ``escopo`` é o nome da URL Django da lista (ex.: ``cadastro:lista_municipios``)
    e ``parametros`` armazena a query string completa (ex.: ``regiao=sudeste&uf=SP``).
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='filtros_salvos',
        verbose_name='usuario',
    )
    escopo = models.CharField(
        'escopo (URL name)',
        max_length=100,
        help_text='Nome da URL da lista, ex. cadastro:lista_municipios.',
    )
    nome = models.CharField('nome', max_length=80)
    parametros = models.CharField(
        'parametros (query string)',
        max_length=500,
        help_text='Query string sem o "?" inicial.',
    )
    criado_em = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'filtro salvo'
        verbose_name_plural = 'filtros salvos'
        ordering = ['escopo', 'nome']
        unique_together = ['usuario', 'escopo', 'nome']
        indexes = [
            models.Index(fields=['usuario', 'escopo']),
        ]

    def __str__(self):
        return f'{self.usuario} — {self.escopo} — {self.nome}'


class LogAlteracao(models.Model):
    """Registro imutável de auditoria — grava criação, edição e exclusão de objetos."""

    class TipoAcao(models.TextChoices):
        CRIACAO = 'criacao', 'Criacao'
        EDICAO = 'edicao', 'Edicao'
        EXCLUSAO = 'exclusao', 'Exclusao'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs_alteracao',
        verbose_name='usuario',
    )
    acao = models.CharField(
        'acao',
        max_length=10,
        choices=TipoAcao.choices,
    )
    modelo = models.CharField('modelo', max_length=100)
    objeto_id = models.CharField('ID do objeto', max_length=50)
    objeto_repr = models.CharField('representacao', max_length=255)
    campos_alterados = models.JSONField(
        'campos alterados',
        default=dict,
        blank=True,
        help_text='Dicionario com campo: {antes, depois}',
    )
    data = models.DateTimeField('data', auto_now_add=True)

    class Meta:
        verbose_name = 'log de alteracao'
        verbose_name_plural = 'logs de alteracao'
        ordering = ['-data']

    def __str__(self):
        return f'{self.usuario} — {self.get_acao_display()} — {self.modelo} — {self.objeto_repr}'
