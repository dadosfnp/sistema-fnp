"""Models de cadastro: Pessoa, Município, Pauta, EnvolvimentoPauta e VínculoMunicípio."""

from django.db import models

from aplicacoes.nucleo.models import ModeloBase


class Pessoa(ModeloBase):
    """Pessoa física vinculada à FNP — prefeito, secretário, assessor ou equipe interna."""

    class TipoPessoa(models.TextChoices):
        INTERNO = 'interno', 'Interno'
        PREFEITO = 'prefeito', 'Prefeito(a)'
        VICE_PREFEITO = 'vice_prefeito', 'Vice-prefeito(a)'
        SECRETARIO = 'secretario', 'Secretário(a)'
        ASSESSOR = 'assessor', 'Assessor(a)'
        VEREADOR = 'vereador', 'Vereador(a)'
        OUTRO = 'outro', 'Outro'

    class Genero(models.TextChoices):
        MASCULINO = 'masculino', 'Masculino'
        FEMININO = 'feminino', 'Feminino'
        OUTRO = 'outro', 'Outro'
        NAO_INFORMADO = 'nao_informado', 'Não informado'

    nome = models.CharField('nome', max_length=255)
    email = models.EmailField('e-mail', unique=True, blank=True, null=True)
    telefone = models.CharField('telefone', max_length=20, blank=True)
    foto = models.ImageField('foto', upload_to='pessoas/fotos/', blank=True)
    tipo = models.CharField(
        'tipo',
        max_length=20,
        choices=TipoPessoa.choices,
        default=TipoPessoa.OUTRO,
    )
    cargo = models.CharField('cargo', max_length=150, blank=True)
    partido = models.CharField('partido', max_length=50, blank=True)
    genero = models.CharField(
        'gênero',
        max_length=20,
        choices=Genero.choices,
        default=Genero.NAO_INFORMADO,
    )
    redes_sociais = models.JSONField(
        'redes sociais',
        default=dict,
        blank=True,
        help_text='Ex: {"instagram": "@prefeito", "twitter": "@prefeito"}',
    )
    biografia_curta = models.TextField('biografia curta', blank=True)
    mandato_inicio = models.DateField('início do mandato', blank=True, null=True)
    mandato_fim = models.DateField('fim do mandato', blank=True, null=True)
    observacoes = models.TextField('observações', blank=True)
    ativo = models.BooleanField('ativo', default=True)

    class Meta:
        verbose_name = 'pessoa'
        verbose_name_plural = 'pessoas'
        ordering = ['nome']

    def __str__(self):
        return self.nome

    @property
    def mandato_vigente(self):
        """Retorna True se a data atual está dentro do período de mandato."""
        from django.utils import timezone
        hoje = timezone.now().date()
        if self.mandato_inicio and self.mandato_fim:
            return self.mandato_inicio <= hoje <= self.mandato_fim
        return False


class Municipio(ModeloBase):
    """Município brasileiro com dados geográficos, demográficos e vínculo FNP."""

    UF_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'),
        ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'),
        ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'),
        ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
        ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'),
        ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'),
        ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
    ]

    class Regiao(models.TextChoices):
        NORTE = 'norte', 'Norte'
        NORDESTE = 'nordeste', 'Nordeste'
        CENTRO_OESTE = 'centro_oeste', 'Centro-Oeste'
        SUDESTE = 'sudeste', 'Sudeste'
        SUL = 'sul', 'Sul'

    nome = models.CharField('nome', max_length=255)
    uf = models.CharField('UF', max_length=2, choices=UF_CHOICES)
    codigo_ibge = models.IntegerField('código IBGE', unique=True)
    populacao = models.IntegerField('população', default=0)
    regiao = models.CharField(
        'região',
        max_length=20,
        choices=Regiao.choices,
        blank=True,
    )
    brasao = models.ImageField('brasao', upload_to='municipios/brasoes/', blank=True)
    eh_capital = models.BooleanField('é capital?', default=False)
    associado_fnp = models.BooleanField('associado FNP?', default=False)
    latitude = models.DecimalField(
        'latitude',
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
    )
    longitude = models.DecimalField(
        'longitude',
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'município'
        verbose_name_plural = 'municípios'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome}/{self.uf}'

    @property
    def adimplencia_atual(self):
        """Retorna o status de adimplencia do ano mais recente, ou None."""
        adimplencia = self.adimplencias.order_by('-ano_referencia').first()
        return adimplencia.status if adimplencia else None


class Pauta(ModeloBase):
    """Eixo temático institucional da FNP (ex.: saúde, mobilidade, segurança)."""

    nome = models.CharField('nome', max_length=100, unique=True)
    descricao = models.TextField('descrição', blank=True)
    icone = models.CharField('ícone', max_length=50, blank=True, help_text='Nome do ícone (ex: heart, book)')
    ativa = models.BooleanField('ativa?', default=True)

    class Meta:
        verbose_name = 'pauta'
        verbose_name_plural = 'pautas'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class EnvolvimentoPauta(ModeloBase):
    """Relação N:N entre Pessoa e Pauta com nível de envolvimento (apoiador/engajado/líder)."""

    class NivelEnvolvimento(models.TextChoices):
        APOIADOR = 'apoiador', 'Apoiador'
        ENGAJADO = 'engajado', 'Engajado'
        LIDER = 'lider', 'Líder'

    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name='envolvimentos_pauta',
        verbose_name='pessoa',
    )
    pauta = models.ForeignKey(
        Pauta,
        on_delete=models.CASCADE,
        related_name='envolvimentos',
        verbose_name='pauta',
    )
    nivel = models.CharField(
        'nível de envolvimento',
        max_length=20,
        choices=NivelEnvolvimento.choices,
        default=NivelEnvolvimento.APOIADOR,
    )
    observacao = models.TextField('observação', blank=True)

    class Meta:
        verbose_name = 'envolvimento em pauta'
        verbose_name_plural = 'envolvimentos em pautas'
        unique_together = ['pessoa', 'pauta']

    def __str__(self):
        return f'{self.pessoa} — {self.pauta} ({self.get_nivel_display()})'


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
        Pessoa,
        on_delete=models.CASCADE,
        related_name='vinculos',
        verbose_name='pessoa',
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.CASCADE,
        related_name='vinculos',
        verbose_name='município',
    )
    papel = models.CharField(
        'papel',
        max_length=20,
        choices=Papel.choices,
    )
    inicio_mandato = models.DateField('início do mandato', blank=True, null=True)
    fim_mandato = models.DateField('fim do mandato', blank=True, null=True)
    vigente = models.BooleanField('vigente?', default=True)
    observacao = models.TextField('observação', blank=True)

    class Meta:
        verbose_name = 'vínculo com município'
        verbose_name_plural = 'vínculos com municípios'
        ordering = ['-vigente', '-inicio_mandato']
        unique_together = ['pessoa', 'municipio', 'papel', 'inicio_mandato']

    def __str__(self):
        return f'{self.pessoa} — {self.get_papel_display()} em {self.municipio}'
