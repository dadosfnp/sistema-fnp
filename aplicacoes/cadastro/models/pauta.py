"""Models Pauta e EnvolvimentoPauta — eixos temáticos e envolvimento de pessoas."""

from django.db import models

from aplicacoes.nucleo.models import ModeloBase

from .pessoa import Pessoa


class Pauta(ModeloBase):
    """Eixo temático institucional da FNP (ex.: saúde, mobilidade, segurança)."""

    nome = models.CharField('nome', max_length=100, unique=True)
    descricao = models.TextField('descrição', blank=True)
    icone = models.CharField('ícone', max_length=50, blank=True, help_text='Nome do ícone (ex: heart, book)')
    ativa = models.BooleanField('ativa?', default=True)

    class Meta:
        app_label = 'cadastro'
        verbose_name = 'pauta'
        verbose_name_plural = 'pautas'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class EnvolvimentoPauta(ModeloBase):
    """Relação N:N entre Pessoa e Pauta com nível de envolvimento (apoiador/engajado/líder)."""

    class NivelEnvolvimento(models.TextChoices):
        APOIADOR = 'apoiador', 'Apoiador'
        ENGAJADO = 'engajado', 'Engajado'
        LIDER = 'lider', 'Líder'

    pessoa = models.ForeignKey(
        Pessoa, on_delete=models.CASCADE,
        related_name='envolvimentos_pauta', verbose_name='pessoa',
    )
    pauta = models.ForeignKey(
        Pauta, on_delete=models.CASCADE,
        related_name='envolvimentos', verbose_name='pauta',
    )
    nivel = models.CharField(
        'nível de envolvimento', max_length=20,
        choices=NivelEnvolvimento.choices, default=NivelEnvolvimento.APOIADOR,
    )
    observacao = models.TextField('observação', blank=True)

    class Meta:
        app_label = 'cadastro'
        verbose_name = 'envolvimento em pauta'
        verbose_name_plural = 'envolvimentos em pautas'
        unique_together = ['pessoa', 'pauta']

    def __str__(self):
        return f'{self.pessoa} — {self.pauta} ({self.get_nivel_display()})'
