"""Model do Dicionário institucional — termos do sistema FNP com definições.

Centraliza as definições da máscara FNP (aba "Dicionario" da planilha de
monitoramento) e serve de referência para quem está usando o sistema pela
primeira vez. Termos são agrupados por seção para facilitar a navegação.
"""

from django.db import models

from aplicacoes.nucleo.models import ModeloBase


class TermoDicionario(ModeloBase):
    """Termo conceitual do sistema com definição e exemplos de tipo de dado.

    Cada termo pertence a uma seção temática (Instâncias, Representantes,
    Atividades, Eventos, Geral). A ordem dentro da seção é controlada
    pelo campo ``ordem``.
    """

    class Secao(models.TextChoices):
        INSTANCIAS = 'instancias', 'Sobre as Instâncias'
        REPRESENTANTES = 'representantes', 'Sobre os Representantes'
        ATIVIDADES = 'atividades', 'Sobre as Atividades'
        EVENTOS = 'eventos', 'Sobre os Eventos'
        PROJETOS = 'projetos', 'Sobre os Projetos'
        MISSOES = 'missoes', 'Sobre as Missões'
        GERAL = 'geral', 'Geral'

    termo = models.CharField('termo', max_length=200, unique=True)
    secao = models.CharField(
        'seção',
        max_length=20,
        choices=Secao.choices,
        default=Secao.GERAL,
    )
    definicao = models.TextField('definição')
    tipo_de_dado = models.CharField(
        'tipo de dado / exemplos',
        max_length=500,
        blank=True,
        help_text='Exemplos de valores possíveis ou formato esperado.',
    )
    ordem = models.PositiveIntegerField(
        'ordem na seção',
        default=100,
        help_text='Menor valor aparece primeiro na seção.',
    )
    ativo = models.BooleanField('ativo?', default=True)

    class Meta:
        verbose_name = 'termo do dicionário'
        verbose_name_plural = 'termos do dicionário'
        ordering = ['secao', 'ordem', 'termo']

    def __str__(self):
        return self.termo
