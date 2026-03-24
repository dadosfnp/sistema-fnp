from django.db import models

from aplicacoes.cadastro.models import Municipio
from aplicacoes.nucleo.models import ModeloBase


class Engajamento(ModeloBase):
    """Pontuação de engajamento de um município."""

    class Nivel(models.TextChoices):
        ALTO = 'alto', 'Alto'
        MEDIO = 'medio', 'Médio'
        BAIXO = 'baixo', 'Baixo'
        INATIVO = 'inativo', 'Inativo'

    municipio = models.OneToOneField(
        Municipio,
        on_delete=models.CASCADE,
        related_name='engajamento',
        verbose_name='município',
    )
    pontuacao_total = models.IntegerField('pontuação total', default=0)
    total_participacoes = models.IntegerField('total de participações', default=0)
    ultima_interacao = models.DateTimeField('última interação', blank=True, null=True)
    nivel = models.CharField(
        'nível',
        max_length=10,
        choices=Nivel.choices,
        default=Nivel.INATIVO,
    )

    class Meta:
        verbose_name = 'engajamento'
        verbose_name_plural = 'engajamentos'
        ordering = ['-pontuacao_total']

    def __str__(self):
        return f'{self.municipio} — {self.get_nivel_display()} ({self.pontuacao_total} pts)'

    def recalcular_nivel(self):
        """Recalcula o nível com base na pontuação total."""
        if self.pontuacao_total >= 80:
            self.nivel = self.Nivel.ALTO
        elif self.pontuacao_total >= 40:
            self.nivel = self.Nivel.MEDIO
        elif self.pontuacao_total >= 10:
            self.nivel = self.Nivel.BAIXO
        else:
            self.nivel = self.Nivel.INATIVO
