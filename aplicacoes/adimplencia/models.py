"""Model de adimplência — controle anual de pagamentos dos municípios à FNP."""

from django.db import models

from aplicacoes.cadastro.models import Municipio
from aplicacoes.nucleo.models import ModeloBase


class Adimplencia(ModeloBase):
    """Registro anual de adimplência de um município (adimplente/inadimplente/parcial)."""

    class Status(models.TextChoices):
        ADIMPLENTE = 'adimplente', 'Adimplente'
        INADIMPLENTE = 'inadimplente', 'Inadimplente'
        PARCIAL = 'parcial', 'Parcial'

    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.CASCADE,
        related_name='adimplencias',
        verbose_name='município',
    )
    ano_referencia = models.IntegerField('ano de referência')
    status = models.CharField(
        'status',
        max_length=20,
        choices=Status.choices,
        default=Status.INADIMPLENTE,
    )
    valor_devido = models.DecimalField(
        'valor devido',
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    valor_pago = models.DecimalField(
        'valor pago',
        max_digits=12,
        decimal_places=2,
        default=0,
    )
    data_pagamento = models.DateField('data do pagamento', blank=True, null=True)
    observacao = models.TextField('observação', blank=True)

    class Meta:
        verbose_name = 'adimplência'
        verbose_name_plural = 'adimplências'
        ordering = ['-ano_referencia']
        unique_together = ['municipio', 'ano_referencia']

    def __str__(self):
        return f'{self.municipio} — {self.ano_referencia} ({self.get_status_display()})'
