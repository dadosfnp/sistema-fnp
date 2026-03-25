from django.db import models

from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.nucleo.models import ModeloBase


class Evento(ModeloBase):
    """Evento institucional da FNP."""

    class TipoEvento(models.TextChoices):
        REUNIAO_GERAL = 'reuniao_geral', 'Reunião Geral da FNP'
        FORUM = 'forum', 'Fórum'
        CONGRESSO = 'congresso', 'Congresso'
        VIAGEM_INTERNACIONAL = 'viagem_internacional', 'Viagem internacional'
        VIAGEM_NACIONAL = 'viagem_nacional', 'Viagem nacional'
        REUNIAO_PRESENCIAL = 'reuniao_presencial', 'Reunião presencial na FNP'
        REUNIAO_ONLINE = 'reuniao_online', 'Reunião online'
        WEBINAR = 'webinar', 'Webinar'
        PRESENCA_FNP = 'presenca_fnp', 'Presença na FNP'

    class Modalidade(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        ONLINE = 'online', 'Online'
        HIBRIDO = 'hibrido', 'Híbrido'

    titulo = models.CharField('título', max_length=255)
    tipo = models.CharField(
        'tipo',
        max_length=25,
        choices=TipoEvento.choices,
    )
    modalidade = models.CharField(
        'modalidade',
        max_length=15,
        choices=Modalidade.choices,
        default=Modalidade.PRESENCIAL,
    )
    data_inicio = models.DateField('data de início')
    data_fim = models.DateField('data de término', blank=True, null=True)
    local = models.CharField('local', max_length=255, blank=True)
    descricao = models.TextField('descrição', blank=True)
    pontos_presencial = models.IntegerField(
        'pontos (presencial)',
        default=10,
        help_text='Pontos para participação presencial.',
    )
    pontos_online = models.IntegerField(
        'pontos (online)',
        default=5,
        help_text='Pontos para participação online. 0 se não aplicável.',
    )
    pontos_palestrante_bonus = models.IntegerField(
        'bônus palestrante',
        default=5,
        help_text='Pontos extras para quem palestrou.',
    )
    pontos_organizador_bonus = models.IntegerField(
        'bônus organizador',
        default=5,
        help_text='Pontos extras para quem organizou.',
    )

    class Meta:
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'{self.titulo} ({self.get_tipo_display()})'


class Participacao(ModeloBase):
    """Registro de participação de uma pessoa em um evento."""

    class FormaParticipacao(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        ONLINE = 'online', 'Online'

    class PapelNoEvento(models.TextChoices):
        PARTICIPANTE = 'participante', 'Participante'
        PALESTRANTE = 'palestrante', 'Palestrante'
        ORGANIZADOR = 'organizador', 'Organizador(a)'
        MODERADOR = 'moderador', 'Moderador(a)'

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
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.CASCADE,
        related_name='participacoes',
        verbose_name='município que recebe os pontos',
        help_text='Município que será pontuado por esta participação.',
    )
    forma_participacao = models.CharField(
        'forma de participação',
        max_length=15,
        choices=FormaParticipacao.choices,
        default=FormaParticipacao.PRESENCIAL,
    )
    papel_no_evento = models.CharField(
        'papel no evento',
        max_length=15,
        choices=PapelNoEvento.choices,
        default=PapelNoEvento.PARTICIPANTE,
    )
    confirmado = models.BooleanField('confirmado?', default=False)
    pontos_calculados = models.IntegerField(
        'pontos calculados',
        default=0,
        help_text='Pontos atribuídos automaticamente ao salvar.',
    )
    data_confirmacao = models.DateTimeField('data de confirmação', blank=True, null=True)

    class Meta:
        verbose_name = 'participação'
        verbose_name_plural = 'participações'
        ordering = ['-criado_em']
        unique_together = ['pessoa', 'evento']

    def __str__(self):
        return f'{self.pessoa} em {self.evento}'

    def calcular_pontos(self):
        """Calcula pontos com base no evento, forma e papel."""
        evento = self.evento
        if self.forma_participacao == self.FormaParticipacao.PRESENCIAL:
            pontos = evento.pontos_presencial
        else:
            pontos = evento.pontos_online

        if self.papel_no_evento == self.PapelNoEvento.PALESTRANTE:
            pontos += evento.pontos_palestrante_bonus
        elif self.papel_no_evento == self.PapelNoEvento.ORGANIZADOR:
            pontos += evento.pontos_organizador_bonus

        return pontos

    def save(self, *args, **kwargs):
        self.pontos_calculados = self.calcular_pontos()
        super().save(*args, **kwargs)
