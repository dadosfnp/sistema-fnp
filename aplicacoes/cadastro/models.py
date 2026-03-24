from django.db import models

from aplicacoes.nucleo.models import ModeloBase


class Pessoa(ModeloBase):
    """Pessoa vinculada à FNP (equipe interna, prefeito, secretário, etc.)."""

    class TipoPessoa(models.TextChoices):
        INTERNO = 'interno', 'Interno'
        PREFEITO = 'prefeito', 'Prefeito(a)'
        SECRETARIO = 'secretario', 'Secretário(a)'
        ASSESSOR = 'assessor', 'Assessor(a)'
        OUTRO = 'outro', 'Outro'

    nome = models.CharField('nome', max_length=255)
    email = models.EmailField('e-mail', unique=True, blank=True, null=True)
    telefone = models.CharField('telefone', max_length=20, blank=True)
    tipo = models.CharField(
        'tipo',
        max_length=20,
        choices=TipoPessoa.choices,
        default=TipoPessoa.OUTRO,
    )
    cargo = models.CharField('cargo', max_length=150, blank=True)
    partido = models.CharField('partido', max_length=50, blank=True)
    ativo = models.BooleanField('ativo', default=True)

    class Meta:
        verbose_name = 'pessoa'
        verbose_name_plural = 'pessoas'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Municipio(ModeloBase):
    """Município brasileiro, possivelmente associado à FNP."""

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

    nome = models.CharField('nome', max_length=255)
    uf = models.CharField('UF', max_length=2, choices=UF_CHOICES)
    codigo_ibge = models.IntegerField('código IBGE', unique=True)
    populacao = models.IntegerField('população', default=0)
    regiao = models.CharField('região', max_length=50, blank=True)
    eh_capital = models.BooleanField('é capital?', default=False)
    associado_fnp = models.BooleanField('associado FNP?', default=False)

    class Meta:
        verbose_name = 'município'
        verbose_name_plural = 'municípios'
        ordering = ['nome']

    def __str__(self):
        return f'{self.nome}/{self.uf}'


class VinculoMunicipio(ModeloBase):
    """Vínculo entre uma pessoa e um município (mandato, cargo, etc.)."""

    class Papel(models.TextChoices):
        PREFEITO = 'prefeito', 'Prefeito(a)'
        SECRETARIO = 'secretario', 'Secretário(a)'
        ASSESSOR = 'assessor', 'Assessor(a)'
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
