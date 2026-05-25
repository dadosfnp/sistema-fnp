"""Model Pessoa — indivíduo vinculado à FNP."""

from django.db import models

from aplicacoes.nucleo.models import ModeloBase
from aplicacoes.nucleo.validators import validar_imagem_segura


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
    foto = models.ImageField(
        'foto', upload_to='pessoas/fotos/', blank=True,
        validators=[validar_imagem_segura],
    )
    tipo = models.CharField(
        'tipo', max_length=20,
        choices=TipoPessoa.choices, default=TipoPessoa.OUTRO,
    )
    cargo = models.CharField('cargo', max_length=150, blank=True)
    partido = models.CharField('partido', max_length=50, blank=True)
    genero = models.CharField(
        'gênero', max_length=20,
        choices=Genero.choices, default=Genero.NAO_INFORMADO,
    )
    redes_sociais = models.JSONField(
        'redes sociais', default=dict, blank=True,
        help_text='Ex: {"instagram": "@prefeito", "twitter": "@prefeito"}',
    )
    biografia_curta = models.TextField('biografia curta', blank=True)
    mandato_inicio = models.DateField('início do mandato', blank=True, null=True)
    mandato_fim = models.DateField('fim do mandato', blank=True, null=True)
    observacoes = models.TextField('observações', blank=True)
    ativo = models.BooleanField('ativo', default=True)
    autorizacao_uso_imagem = models.BooleanField(
        'autorização de uso de imagem', default=False,
        help_text='Termo de autorização assinado para uso da imagem em comunicações da FNP.',
    )
    termo_confidencialidade = models.BooleanField(
        'termo de confidencialidade', default=False,
        help_text='Termo de confidencialidade assinado quando aplicável à função na FNP.',
    )

    class Meta:
        app_label = 'cadastro'
        verbose_name = 'pessoa'
        verbose_name_plural = 'pessoas'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['nome']),
            models.Index(fields=['tipo']),
            models.Index(fields=['ativo']),
            models.Index(fields=['email']),
        ]

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
