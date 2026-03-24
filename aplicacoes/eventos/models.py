from django.db import models

from aplicacoes.cadastro.models import Pessoa
from aplicacoes.nucleo.models import ModeloBase


class Evento(ModeloBase):
    """Evento institucional da FNP (fórum, reunião, webinar, etc.)."""

    class TipoEvento(models.TextChoices):
        FORUM = 'forum', 'Fórum'
        REUNIAO = 'reuniao', 'Reunião'
        EVENTO_PRESENCIAL = 'evento_presencial', 'Evento presencial'
        WEBINAR = 'webinar', 'Webinar'

    titulo = models.CharField('título', max_length=255)
    tipo = models.CharField(
        'tipo',
        max_length=20,
        choices=TipoEvento.choices,
    )
    data_inicio = models.DateField('data de início')
    data_fim = models.DateField('data de término', blank=True, null=True)
    local = models.CharField('local', max_length=255, blank=True)
    descricao = models.TextField('descrição', blank=True)
    peso_engajamento = models.IntegerField(
        'peso no engajamento',
        default=10,
        help_text='Pontos atribuídos ao município por cada participação neste evento.',
    )

    class Meta:
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'{self.titulo} ({self.get_tipo_display()})'


class Participacao(ModeloBase):
    """Registro de participação de uma pessoa em um evento."""

    class TipoParticipacao(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        VIRTUAL = 'virtual', 'Virtual'
        PALESTRANTE = 'palestrante', 'Palestrante'
        ORGANIZADOR = 'organizador', 'Organizador(a)'

    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name='participacoes',
        verbose_name='pessoa',
    )
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='participacoes',
        verbose_name='evento',
    )
    tipo_participacao = models.CharField(
        'tipo de participação',
        max_length=20,
        choices=TipoParticipacao.choices,
        default=TipoParticipacao.PRESENCIAL,
    )
    confirmado = models.BooleanField('confirmado?', default=False)
    data_confirmacao = models.DateTimeField('data de confirmação', blank=True, null=True)

    class Meta:
        verbose_name = 'participação'
        verbose_name_plural = 'participações'
        ordering = ['-criado_em']
        unique_together = ['pessoa', 'evento']

    def __str__(self):
        return f'{self.pessoa} em {self.evento}'
