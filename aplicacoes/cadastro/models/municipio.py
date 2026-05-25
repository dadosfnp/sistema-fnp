"""Model Municipio — entidade geográfica brasileira com vínculo FNP."""

from django.db import models

from aplicacoes.nucleo.models import ModeloBase
from aplicacoes.nucleo.validators import validar_imagem_segura


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
        'região', max_length=20, choices=Regiao.choices, blank=True,
    )
    brasao = models.ImageField(
        'brasao', upload_to='municipios/brasoes/', blank=True,
        validators=[validar_imagem_segura],
    )
    eh_capital = models.BooleanField('é capital?', default=False)
    associado_fnp = models.BooleanField('associado FNP?', default=False)
    regiao_metropolitana = models.CharField(
        'região metropolitana', max_length=80, blank=True,
        help_text='Nome da Região Metropolitana se o município faz parte (ex: RM de São Paulo).',
    )
    latitude = models.DecimalField('latitude', max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField('longitude', max_digits=10, decimal_places=7, blank=True, null=True)

    class Meta:
        app_label = 'cadastro'
        verbose_name = 'município'
        verbose_name_plural = 'municípios'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['uf']),
            models.Index(fields=['regiao']),
            models.Index(fields=['associado_fnp']),
            models.Index(fields=['codigo_ibge']),
        ]

    def __str__(self):
        return f'{self.nome}/{self.uf}'

    @property
    def adimplencia_atual(self):
        """Retorna o status de adimplencia do ano mais recente, ou None."""
        adimplencia = self.adimplencias.order_by('-ano_referencia').first()
        return adimplencia.status if adimplencia else None
