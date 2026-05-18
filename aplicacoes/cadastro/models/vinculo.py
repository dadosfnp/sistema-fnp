"""Model VinculoMunicipio — relação formal entre Pessoa e Município."""

from django.db import models

from aplicacoes.nucleo.models import ModeloBase

from .municipio import Municipio
from .pessoa import Pessoa


class VinculoMunicipio(ModeloBase):
    """Vínculo formal entre uma Pessoa e um Município — define papel e período de mandato."""

    class Papel(models.TextChoices):
        PREFEITO = 'prefeito', 'Prefeito(a)'
        VICE_PREFEITO = 'vice_prefeito', 'Vice-prefeito(a)'
        SECRETARIO = 'secretario', 'Secretário(a)'
        ASSESSOR = 'assessor', 'Assessor(a)'
        VEREADOR = 'vereador', 'Vereador(a)'
        CONTATO = 'contato', 'Contato'

    pessoa = models.ForeignKey(
        Pessoa, on_delete=models.CASCADE,
        related_name='vinculos', verbose_name='pessoa',
    )
    municipio = models.ForeignKey(
        Municipio, on_delete=models.CASCADE,
        related_name='vinculos', verbose_name='município',
    )
    papel = models.CharField('papel', max_length=20, choices=Papel.choices)
    inicio_mandato = models.DateField('início do mandato', blank=True, null=True)
    fim_mandato = models.DateField('fim do mandato', blank=True, null=True)
    vigente = models.BooleanField('vigente?', default=True)
    observacao = models.TextField('observação', blank=True)

    class Meta:
        app_label = 'cadastro'
        verbose_name = 'vínculo com município'
        verbose_name_plural = 'vínculos com municípios'
        ordering = ['-vigente', '-inicio_mandato']
        unique_together = ['pessoa', 'municipio', 'papel', 'inicio_mandato']
        indexes = [
            models.Index(fields=['vigente']),
            models.Index(fields=['pessoa', 'vigente']),
            models.Index(fields=['municipio', 'vigente']),
        ]

    def __str__(self):
        return f'{self.pessoa} — {self.get_papel_display()} em {self.municipio}'
