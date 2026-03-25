import uuid

from django.conf import settings
from django.db import models


class ModeloBase(models.Model):
    """Modelo abstrato base para todos os models do sistema."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    criado_em = models.DateTimeField('criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        abstract = True


class Perfil(models.Model):
    """Perfil do usuario com nivel de acesso ao sistema."""

    class TipoPerfil(models.TextChoices):
        VISUALIZADOR = 'visualizador', 'Visualizador'
        EDITOR = 'editor', 'Editor'

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

    class Meta:
        verbose_name = 'perfil'
        verbose_name_plural = 'perfis'

    def __str__(self):
        return f'{self.usuario.get_full_name() or self.usuario.username} — {self.get_tipo_display()}'

    @property
    def eh_editor(self):
        return self.tipo == self.TipoPerfil.EDITOR


class LogAlteracao(models.Model):
    """Registro de auditoria — quem alterou o que e quando."""

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
