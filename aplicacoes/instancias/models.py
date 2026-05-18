"""Models de Espaços de Diálogo Federativo (Instâncias) e Representações.

Mapeamento dos campos a partir da máscara FNP (aba "Instâncias" e "Representantes"):
- Instância = estrutura institucional (Conselho, Comitê, Comissão, Fórum, Associação, Rede)
- Representação = vínculo de uma Pessoa a uma Instância (titular/suplente etc.)
"""

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from aplicacoes.cadastro.models import Pessoa
from aplicacoes.nucleo.models import ModeloBase


class Instancia(ModeloBase):
    """Espaço de Diálogo Federativo onde a FNP atua ou tem representação.

    Engloba comissões internas, fóruns, conselhos e demais espaços com tomada de
    decisão coletiva. Cada instância tem um arcabouço legal, periodicidade de
    reuniões e composição definida em número de representantes por esfera.
    """

    class Origem(models.TextChoices):
        INTERNA = 'interna', 'Interna'
        EXTERNA = 'externa', 'Externa'
        EVENTO = 'evento', 'Evento'

    class Forma(models.TextChoices):
        COMISSAO = 'comissao', 'Comissão'
        FORUM = 'forum', 'Fórum'
        COM_REPRESENTACAO = 'com_representacao', 'Com representação'
        SEM_REPRESENTACAO = 'sem_representacao', 'Sem representação'
        REUNIAO_GERAL = 'reuniao_geral', 'Reunião Geral'

    class Categoria(models.TextChoices):
        PRINCIPAL = 'principal', 'Principal'
        SECUNDARIA = 'secundaria', 'Secundária'

    class TipoArcabouco(models.TextChoices):
        LEI_FEDERAL = 'lei_federal', 'Lei federal'
        LEI_COMPLEMENTAR = 'lei_complementar', 'Lei complementar'
        DECRETO = 'decreto', 'Decreto'
        PORTARIA_MINISTERIAL = 'portaria_ministerial', 'Portaria Ministerial'
        PORTARIA_INTERMINISTERIAL = 'portaria_interministerial', 'Portaria Interministerial'
        REGIMENTO = 'regimento', 'Regimento Interno / Estatuto'
        OUTRO = 'outro', 'Outro'

    class Status(models.TextChoices):
        EM_CONSTRUCAO = 'em_construcao', 'Em construção'
        EM_FUNCIONAMENTO = 'em_funcionamento', 'Em funcionamento'
        INATIVO = 'inativo', 'Inativo'

    class TempoMandato(models.TextChoices):
        UM_ANO = '1_ano', '1 ano'
        DOIS_ANOS = '2_anos', '2 anos'
        TRES_ANOS = '3_anos', '3 anos'
        QUATRO_ANOS = '4_anos', '4 anos'
        SEM_PREVISAO = 'sem_previsao', 'Sem previsão regimental'

    class Periodicidade(models.TextChoices):
        SEMANAL = 'semanal', 'Semanal'
        MENSAL = 'mensal', 'Mensal'
        BIMESTRAL = 'bimestral', 'Bimestral'
        TRIMESTRAL = 'trimestral', 'Trimestral'
        SEMESTRAL = 'semestral', 'Semestral'
        EM_DEFINICAO = 'em_definicao', 'Em definição'

    nome = models.CharField('nome do espaço', max_length=255)
    origem = models.CharField(
        'origem',
        max_length=10,
        choices=Origem.choices,
        help_text='Interna (criada pela FNP) | Externa (espaço de outro órgão) | Evento.',
    )
    forma = models.CharField(
        'forma do espaço',
        max_length=20,
        choices=Forma.choices,
    )
    categoria = models.CharField(
        'categoria',
        max_length=15,
        choices=Categoria.choices,
        default=Categoria.PRINCIPAL,
        help_text='Principal (a instância em si) | Secundária (GT, CT, subcomissão).',
    )
    instancia_principal = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subgrupos',
        verbose_name='instância principal',
        help_text='Preencher quando esta for um GT/CT/subcomissão vinculada a uma instância maior.',
    )
    tipo_arcabouco = models.CharField(
        'tipo do arcabouço legal',
        max_length=30,
        choices=TipoArcabouco.choices,
        blank=True,
    )
    numero_arcabouco = models.CharField(
        'identificação do arcabouço',
        max_length=100,
        blank=True,
        help_text='Ex.: Lei 3434/2020, Decreto 7890/2021, Portaria 45/2024.',
    )
    link_arcabouco = models.URLField('link do arcabouço legal', blank=True)
    status = models.CharField(
        'status',
        max_length=20,
        choices=Status.choices,
        default=Status.EM_FUNCIONAMENTO,
    )
    composicao = models.JSONField(
        'composição',
        default=dict,
        blank=True,
        help_text='Número de representantes por esfera. Ex.: {"federal": 2, "estadual": 3, "municipal": 5, "sociedade_civil": 2}.',
    )
    tempo_mandato = models.CharField(
        'tempo do mandato',
        max_length=15,
        choices=TempoMandato.choices,
        blank=True,
    )
    periodicidade_reunioes = models.CharField(
        'periodicidade das reuniões',
        max_length=15,
        choices=Periodicidade.choices,
        blank=True,
    )
    possui_gt_ct = models.BooleanField(
        'possui GT/CT?',
        default=False,
        help_text='Possui Grupos de Trabalho e/ou Comitês Temáticos.',
    )
    link_site = models.URLField('link do site', blank=True)
    ponto_focal_fnp = models.ForeignKey(
        Pessoa,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instancias_como_ponto_focal',
        verbose_name='ponto focal FNP',
        limit_choices_to={'tipo': 'interno'},
        help_text='Profissional técnico da FNP responsável por apoiar e acompanhar esta instância.',
    )
    descricao = models.TextField('descrição', blank=True)
    documentos = GenericRelation(
        'documentos.Documento',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='instancia',
    )

    class Meta:
        verbose_name = 'instância'
        verbose_name_plural = 'instâncias'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['origem']),
            models.Index(fields=['status']),
            models.Index(fields=['origem', 'status']),
        ]

    def __str__(self):
        return self.nome


class Representacao(ModeloBase):
    """Vínculo formal de uma Pessoa a uma Instância (titular, suplente, presidência etc.).

    Substitui o conceito antigo de "envolvimento" isolado em pauta — aqui a
    representação é específica a uma instância e tem mandato com datas próprias.
    """

    class Funcao(models.TextChoices):
        TITULAR = 'titular', 'Titular'
        SUPLENTE = 'suplente', 'Suplente'
        PRESIDENTE = 'presidente', 'Presidente'
        VICE_PRESIDENTE = 'vice_presidente', 'Vice-presidente'
        SECRETARIO_GERAL = 'secretario_geral', 'Secretário(a) Geral'
        SECRETARIO_EXECUTIVO = 'secretario_executivo', 'Secretário(a)-Executivo(a)'
        DIRETOR_TEMATICO = 'diretor_tematico', 'Diretor(a) Temático(a)'
        DIRETOR_REGIONAL = 'diretor_regional', 'Diretor(a) Regional'
        PARTICIPANTE = 'participante', 'Participante'
        PRIMEIRO_SUPLENTE = 'primeiro_suplente', '1º Suplente'
        SEGUNDO_SUPLENTE = 'segundo_suplente', '2º Suplente'

    class TipoMandato(models.TextChoices):
        PRIMEIRO = 'primeiro', '1º Mandato'
        SEGUNDO = 'segundo', '2º Mandato'
        RECONDUCAO = 'reconducao', 'Recondução'

    class DocumentoIndicacao(models.TextChoices):
        DOU = 'dou', 'Publicação em DOU'
        OFICIO = 'oficio', 'Ofício'
        PORTARIA = 'portaria', 'Portaria'
        EMAIL = 'email', 'E-mail'
        ATA = 'ata', 'Ata'

    instancia = models.ForeignKey(
        Instancia,
        on_delete=models.CASCADE,
        related_name='representacoes',
        verbose_name='instância',
    )
    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name='representacoes',
        verbose_name='representante',
    )
    funcao = models.CharField('função', max_length=25, choices=Funcao.choices)
    tipo_mandato = models.CharField(
        'tipo de mandato',
        max_length=15,
        choices=TipoMandato.choices,
        blank=True,
    )
    documento_indicacao = models.CharField(
        'documento de indicação/nomeação',
        max_length=15,
        choices=DocumentoIndicacao.choices,
        blank=True,
    )
    inicio_mandato = models.DateField('início do mandato', blank=True, null=True)
    fim_mandato = models.DateField('fim do mandato', blank=True, null=True)
    autorizacao_uso_imagem = models.BooleanField(
        'autorização do uso de imagem?',
        default=False,
    )
    termo_confidencialidade = models.BooleanField(
        'termo de confidencialidade assinado?',
        default=False,
    )
    vigente = models.BooleanField('vigente?', default=True)
    observacao = models.TextField('observação', blank=True)

    class Meta:
        verbose_name = 'representação'
        verbose_name_plural = 'representações'
        ordering = ['-vigente', '-inicio_mandato']
        unique_together = ['instancia', 'pessoa', 'funcao', 'inicio_mandato']
        indexes = [
            models.Index(fields=['vigente']),
            models.Index(fields=['instancia', 'vigente']),
            models.Index(fields=['pessoa', 'vigente']),
        ]

    def __str__(self):
        return f'{self.pessoa} — {self.get_funcao_display()} em {self.instancia}'
