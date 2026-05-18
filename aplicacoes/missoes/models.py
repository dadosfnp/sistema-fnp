"""Models de Missões institucionais (nacionais e internacionais).

Uma missão é um deslocamento institucional com objetivo específico — encontros,
viagens, intercâmbios técnicos. Pode ter uma delegação (lista de pessoas que
participaram) e gera registros documentais ao final.
"""

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from aplicacoes.cadastro.models import Pessoa
from aplicacoes.instancias.models import Instancia
from aplicacoes.nucleo.models import ModeloBase


class Missao(ModeloBase):
    """Deslocamento institucional da FNP, nacional ou internacional, com delegação e objetivos."""

    class Tipo(models.TextChoices):
        NACIONAL = 'nacional', 'Nacional'
        INTERNACIONAL = 'internacional', 'Internacional'

    class Status(models.TextChoices):
        PLANEJADA = 'planejada', 'Planejada'
        EM_ANDAMENTO = 'em_andamento', 'Em andamento'
        REALIZADA = 'realizada', 'Realizada'
        CANCELADA = 'cancelada', 'Cancelada'

    titulo = models.CharField('título', max_length=255)
    tipo = models.CharField('tipo', max_length=15, choices=Tipo.choices)
    status = models.CharField(
        'status',
        max_length=15,
        choices=Status.choices,
        default=Status.PLANEJADA,
    )
    pais = models.CharField(
        'país',
        max_length=100,
        blank=True,
        help_text='País de destino. Em missões nacionais, deixar em branco ou preencher "Brasil".',
    )
    cidade = models.CharField('cidade', max_length=150, blank=True)
    objetivo = models.TextField('objetivo', blank=True)
    data_inicio = models.DateField('data de início')
    data_fim = models.DateField('data de término', blank=True, null=True)
    chefe_delegacao = models.ForeignKey(
        Pessoa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='missoes_como_chefe',
        verbose_name='chefe da delegação',
    )
    instancia_vinculada = models.ForeignKey(
        Instancia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='missoes',
        verbose_name='instância vinculada',
    )
    relatorio_resumo = models.TextField(
        'resumo do relatório',
        blank=True,
        help_text='Resumo executivo dos resultados da missão (documentos completos vão no repositório).',
    )
    documentos = GenericRelation(
        'documentos.Documento',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='missao',
    )
    presencas = GenericRelation(
        'presenca.Presenca',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='missao',
    )

    class Meta:
        verbose_name = 'missão'
        verbose_name_plural = 'missões'
        ordering = ['-data_inicio']
        indexes = [
            models.Index(fields=['-data_inicio']),
            models.Index(fields=['tipo']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        local = self.cidade or self.pais or '—'
        return f'{self.titulo} ({local}, {self.data_inicio.year if self.data_inicio else "?"})'


class MembroDelegacao(ModeloBase):
    """Pessoa que integra a delegação de uma missão, com papel definido."""

    class Papel(models.TextChoices):
        CHEFE = 'chefe', 'Chefe da delegação'
        REPRESENTANTE = 'representante', 'Representante institucional'
        TECNICO = 'tecnico', 'Técnico de apoio'
        OBSERVADOR = 'observador', 'Observador'
        CONVIDADO = 'convidado', 'Convidado'

    missao = models.ForeignKey(
        Missao,
        on_delete=models.CASCADE,
        related_name='delegacao',
        verbose_name='missão',
    )
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name='participacoes_missao',
        verbose_name='pessoa',
    )
    papel = models.CharField(
        'papel na missão',
        max_length=20,
        choices=Papel.choices,
        default=Papel.REPRESENTANTE,
    )
    observacao = models.TextField('observação', blank=True)

    class Meta:
        verbose_name = 'membro da delegação'
        verbose_name_plural = 'membros da delegação'
        unique_together = ['missao', 'pessoa']

    def __str__(self):
        return f'{self.pessoa} — {self.get_papel_display()} em {self.missao}'
