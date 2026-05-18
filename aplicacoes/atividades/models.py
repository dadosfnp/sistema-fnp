"""Models de Atividades — reuniões e encontros vinculados a uma Instância.

Conforme aba "Atividade" da máscara FNP, cada atividade é um registro de
reunião com formato (presencial/virtual/híbrida), classificação (ordinária
ou extraordinária) e três documentos canônicos: Pauta, Ata, Lista de Presença.
"""

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from aplicacoes.instancias.models import Instancia
from aplicacoes.nucleo.models import ModeloBase


class Atividade(ModeloBase):
    """Reunião ou encontro de uma Instância, com pauta, ata e lista de presença."""

    class Formato(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        VIRTUAL = 'virtual', 'Virtual'
        HIBRIDA = 'hibrida', 'Híbrida'

    class TipoCalendario(models.TextChoices):
        ORDINARIA = 'ordinaria', 'Ordinária'
        EXTRAORDINARIA = 'extraordinaria', 'Extraordinária'

    class Status(models.TextChoices):
        AGENDADA = 'agendada', 'Agendada'
        REALIZADA = 'realizada', 'Realizada'
        CANCELADA = 'cancelada', 'Cancelada'
        ADIADA = 'adiada', 'Adiada'

    instancia = models.ForeignKey(
        Instancia,
        on_delete=models.CASCADE,
        related_name='atividades',
        verbose_name='instância',
    )
    titulo = models.CharField(
        'título',
        max_length=255,
        blank=True,
        help_text='Opcional. Se vazio, será composto a partir da instância e data.',
    )
    data_reuniao = models.DateField('data da reunião')
    horario = models.TimeField('horário', blank=True, null=True)
    formato = models.CharField(
        'formato',
        max_length=15,
        choices=Formato.choices,
        default=Formato.PRESENCIAL,
    )
    tipo_calendario = models.CharField(
        'tipo de reunião',
        max_length=15,
        choices=TipoCalendario.choices,
        default=TipoCalendario.ORDINARIA,
    )
    status = models.CharField(
        'status',
        max_length=15,
        choices=Status.choices,
        default=Status.AGENDADA,
    )
    local = models.CharField(
        'local / link da reunião',
        max_length=500,
        blank=True,
        help_text='Endereço presencial ou URL da chamada virtual.',
    )
    pauta_resumo = models.TextField(
        'resumo da pauta',
        blank=True,
        help_text='Síntese dos itens. O documento completo vai no repositório de documentos.',
    )
    ata_resumo = models.TextField(
        'resumo da ata',
        blank=True,
        help_text='Síntese das deliberações. O documento completo vai no repositório.',
    )
    possui_pauta = models.BooleanField('possui pauta registrada?', default=False)
    possui_ata = models.BooleanField('possui ata registrada?', default=False)
    possui_lista_presenca = models.BooleanField(
        'possui lista de presença registrada?',
        default=False,
    )
    documentos = GenericRelation(
        'documentos.Documento',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='atividade',
    )
    presencas = GenericRelation(
        'presenca.Presenca',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='atividade',
    )

    class Meta:
        verbose_name = 'atividade'
        verbose_name_plural = 'atividades'
        ordering = ['-data_reuniao']
        indexes = [
            models.Index(fields=['-data_reuniao']),
            models.Index(fields=['instancia', '-data_reuniao']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        if self.titulo:
            return self.titulo
        return f'{self.instancia.nome} — {self.data_reuniao.strftime("%d/%m/%Y") if self.data_reuniao else "?"}'
