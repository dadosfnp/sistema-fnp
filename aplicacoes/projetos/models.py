"""Models de Projetos institucionais da FNP.

Um projeto é uma iniciativa estruturada com começo, meio e fim, objetivos
específicos e responsáveis. Diferente de uma Instância (espaço permanente
de diálogo) e de um Evento (acontecimento pontual), o projeto tem vida
finita e gera entregáveis.
"""

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from aplicacoes.cadastro.models import Pauta, Pessoa
from aplicacoes.instancias.models import Instancia
from aplicacoes.nucleo.models import ModeloBase


class Projeto(ModeloBase):
    """Iniciativa institucional com escopo, prazo e responsáveis definidos."""

    class Status(models.TextChoices):
        PLANEJAMENTO = 'planejamento', 'Em planejamento'
        EM_ANDAMENTO = 'em_andamento', 'Em andamento'
        PAUSADO = 'pausado', 'Pausado'
        CONCLUIDO = 'concluido', 'Concluído'
        CANCELADO = 'cancelado', 'Cancelado'

    class FontesRecurso(models.TextChoices):
        PROPRIO = 'proprio', 'Recurso próprio'
        PARCERIA = 'parceria', 'Parceria'
        CONVENIO = 'convenio', 'Convênio'
        EMENDA = 'emenda', 'Emenda parlamentar'
        INTERNACIONAL = 'internacional', 'Cooperação internacional'
        OUTRO = 'outro', 'Outro'

    nome = models.CharField('nome do projeto', max_length=255)
    descricao = models.TextField('descrição', blank=True)
    objetivo = models.TextField(
        'objetivo',
        blank=True,
        help_text='Resultado pretendido com a execução do projeto.',
    )
    status = models.CharField(
        'status',
        max_length=15,
        choices=Status.choices,
        default=Status.PLANEJAMENTO,
    )
    fonte_recurso = models.CharField(
        'fonte de recurso',
        max_length=15,
        choices=FontesRecurso.choices,
        blank=True,
    )
    valor_orcado = models.DecimalField(
        'valor orçado (R$)',
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
    )
    data_inicio = models.DateField('data de início', blank=True, null=True)
    data_fim_previsto = models.DateField('previsão de término', blank=True, null=True)
    data_fim_real = models.DateField('término real', blank=True, null=True)
    responsavel = models.ForeignKey(
        Pessoa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projetos_responsavel',
        verbose_name='responsável',
        limit_choices_to={'tipo': 'interno'},
    )
    pautas = models.ManyToManyField(
        Pauta,
        blank=True,
        related_name='projetos',
        verbose_name='pautas relacionadas',
    )
    instancia_vinculada = models.ForeignKey(
        Instancia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projetos',
        verbose_name='instância vinculada',
        help_text='Espaço de Diálogo Federativo ao qual o projeto está relacionado, se houver.',
    )
    documentos = GenericRelation(
        'documentos.Documento',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='projeto',
    )

    class Meta:
        verbose_name = 'projeto'
        verbose_name_plural = 'projetos'
        ordering = ['-data_inicio', 'nome']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['-data_inicio']),
            models.Index(fields=['fonte_recurso']),
        ]

    def __str__(self):
        return self.nome
