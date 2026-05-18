"""Models de engajamento — configuração singleton, pesos por categoria e pontuação bienal.

O cálculo final combina contribuições de várias categorias (eventos, instâncias,
missões, atividades) ponderadas por ``PesoEngajamento``. Esse model é a tabela
de "metodologia" editável pela equipe FNP — cada peso pode ser ajustado pelo
admin sem mudança de código.
"""

from django.db import models
from django.utils import timezone

from aplicacoes.cadastro.models import Municipio
from aplicacoes.nucleo.models import ModeloBase


class ConfiguracaoEngajamento(ModeloBase):
    """Singleton com parâmetros globais do cálculo de engajamento (meta, decaimento, penalidades)."""

    bienio_atual = models.CharField(
        'biênio atual',
        max_length=10,
        default='2025-2026',
        help_text='Ex: 2025-2026',
    )
    meta_bienio = models.IntegerField(
        'meta do biênio (pontos)',
        default=200,
        help_text='Pontuação bruta para atingir nota 100.',
    )
    fator_decaimento = models.DecimalField(
        'fator de decaimento anual',
        max_digits=3,
        decimal_places=2,
        default=0.70,
        help_text='Pontos do ano anterior são multiplicados por este fator. Ex: 0.70 = mantém 70%.',
    )
    penalidade_inadimplente = models.DecimalField(
        'penalidade inadimplente (%)',
        max_digits=4,
        decimal_places=2,
        default=0.30,
        help_text='Percentual de perda para inadimplentes. Ex: 0.30 = perde 30%.',
    )
    penalidade_parcial = models.DecimalField(
        'penalidade parcial (%)',
        max_digits=4,
        decimal_places=2,
        default=0.15,
        help_text='Percentual de perda para adimplência parcial. Ex: 0.15 = perde 15%.',
    )

    class Meta:
        verbose_name = 'configuração de engajamento'
        verbose_name_plural = 'configurações de engajamento'

    def __str__(self):
        return f'Configuração — Biênio {self.bienio_atual}'

    def save(self, *args, **kwargs):
        """Garante comportamento singleton reutilizando o PK existente."""
        self.pk = self.pk or ConfiguracaoEngajamento.objects.first() and ConfiguracaoEngajamento.objects.first().pk
        super().save(*args, **kwargs)

    @classmethod
    def atual(cls):
        """Retorna a configuração vigente, criando uma com defaults se necessário."""
        obj, _ = cls.objects.get_or_create(
            pk=cls.objects.first().pk if cls.objects.exists() else None,
            defaults={'bienio_atual': '2025-2026'},
        )
        return obj


class PesoEngajamento(ModeloBase):
    """Peso aplicado a cada tipo de contribuição no cálculo do engajamento.

    Cada linha define quantos pontos um município ganha por uma contribuição
    específica (representação titular, presença em atividade, membro de
    delegação internacional etc.). Editar pelo admin Unfold ou pelo seed
    ``popular_pesos_engajamento``.
    """

    class Chave(models.TextChoices):
        EVENTO_PRESENCIAL = 'evento_presencial', 'Evento — participação presencial'
        EVENTO_ONLINE = 'evento_online', 'Evento — participação online'
        EVENTO_BONUS_PALESTRANTE = 'evento_bonus_palestrante', 'Evento — bônus palestrante'
        EVENTO_BONUS_ORGANIZADOR = 'evento_bonus_organizador', 'Evento — bônus organizador'
        REPRESENTACAO_TITULAR = 'representacao_titular', 'Representação titular vigente'
        REPRESENTACAO_SUPLENTE = 'representacao_suplente', 'Representação suplente vigente'
        REPRESENTACAO_DIRETIVA = 'representacao_diretiva', 'Representação em função diretiva (presidência etc.)'
        PRESENCA_ATIVIDADE = 'presenca_atividade', 'Presença em atividade de instância'
        MISSAO_INTERNACIONAL = 'missao_internacional', 'Membro de delegação internacional'
        MISSAO_NACIONAL = 'missao_nacional', 'Membro de delegação nacional'

    chave = models.CharField('chave', max_length=40, choices=Chave.choices)
    peso = models.IntegerField(
        'peso (pontos)',
        default=10,
        help_text='Quantos pontos esta contribuição vale, antes do decaimento e penalidades.',
    )
    descricao = models.TextField(
        'descrição',
        blank=True,
        help_text='Explicação institucional do peso — aparece na página de metodologia.',
    )
    ativo = models.BooleanField('ativo?', default=True)
    vigente_de = models.DateField(
        'vigente desde',
        null=True, blank=True,
        help_text='Data a partir da qual este peso passa a valer. Vazio = sempre vigente.',
    )
    vigente_ate = models.DateField(
        'vigente até',
        null=True, blank=True,
        help_text='Data até a qual este peso vale. Vazio = sem fim. Mudanças preservam histórico.',
    )

    class Meta:
        verbose_name = 'peso do engajamento'
        verbose_name_plural = 'pesos do engajamento'
        ordering = ['chave', '-vigente_de']
        indexes = [
            models.Index(fields=['chave', 'ativo']),
            models.Index(fields=['vigente_de', 'vigente_ate']),
        ]

    def __str__(self):
        if self.vigente_de or self.vigente_ate:
            return f'{self.get_chave_display()}: {self.peso} pts ({self.vigente_de or "—"} → {self.vigente_ate or "atual"})'
        return f'{self.get_chave_display()}: {self.peso} pts'

    @classmethod
    def valor(cls, chave, fallback=0, na_data=None):
        """Retorna o peso ativo na data informada (ou hoje), ou ``fallback``.

        Vigência: peso conta se ``vigente_de <= data <= vigente_ate`` (limites
        null são tratados como "infinito"). Se houver mais de um vigente, usa
        o mais recente.
        """
        from django.db.models import Q
        from django.utils import timezone

        data = na_data or timezone.now().date()
        qs = cls.objects.filter(chave=chave, ativo=True).filter(
            Q(vigente_de__lte=data) | Q(vigente_de__isnull=True),
        ).filter(
            Q(vigente_ate__gte=data) | Q(vigente_ate__isnull=True),
        ).order_by('-vigente_de')
        peso = qs.first()
        return peso.peso if peso else fallback


class Engajamento(ModeloBase):
    """Score de engajamento de um município em um biênio — calculado a partir de participações."""

    class Nivel(models.TextChoices):
        ALTO = 'alto', 'Alto'
        MEDIO = 'medio', 'Médio'
        BAIXO = 'baixo', 'Baixo'
        INATIVO = 'inativo', 'Inativo'

    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.CASCADE,
        related_name='engajamentos',
        verbose_name='município',
    )
    bienio = models.CharField('biênio', max_length=10, help_text='Ex: 2025-2026')
    pontuacao_bruta = models.IntegerField('pontuação bruta', default=0)
    pontuacao_ano_atual = models.IntegerField('pontos ano atual', default=0)
    pontuacao_ano_anterior = models.IntegerField('pontos ano anterior', default=0)
    penalidade_adimplencia = models.IntegerField('penalidade adimplência', default=0)
    pontuacao_normalizada = models.IntegerField(
        'pontuação normalizada (0-100)',
        default=0,
        help_text='Score final de 0 a 100.',
    )
    total_participacoes = models.IntegerField('total de participações', default=0)
    nivel = models.CharField(
        'nível',
        max_length=10,
        choices=Nivel.choices,
        default=Nivel.INATIVO,
    )
    ultima_atualizacao = models.DateTimeField('última atualização', auto_now=True)

    class Meta:
        verbose_name = 'engajamento'
        verbose_name_plural = 'engajamentos'
        ordering = ['-pontuacao_normalizada']
        unique_together = ['municipio', 'bienio']

    def __str__(self):
        return f'{self.municipio} — {self.bienio} — {self.get_nivel_display()} ({self.pontuacao_normalizada}/100)'

    def recalcular(self):
        """Recalcula a pontuação delegando o agregado ao registry de fontes.

        Cada fonte (eventos, representações, presenças, missões, futuras) está
        em ``aplicacoes.engajamento.servicos.calculo``. Decaimento, normalização
        e penalidade ficam aqui pois são regras transversais do bienio.
        """
        from aplicacoes.adimplencia.models import Adimplencia
        from aplicacoes.engajamento.servicos.calculo import calcular_pontos
        from aplicacoes.eventos.models import Evento

        config = ConfiguracaoEngajamento.atual()
        ano1, ano2 = [int(x) for x in self.bienio.split('-')]
        ano_atual = timezone.now().year

        ano_atual_pts, ano_anterior_pts, total_itens, _ = calcular_pontos(
            self.municipio, ano1, ano2,
        )
        self.pontuacao_ano_atual = ano_atual_pts
        self.pontuacao_ano_anterior = ano_anterior_pts
        self.pontuacao_bruta = int(ano_atual_pts + (ano_anterior_pts * float(config.fator_decaimento)))

        eventos_bienio = Evento.objects.filter(data_inicio__year__in=[ano1, ano2])
        peso_rep_titular = PesoEngajamento.valor(PesoEngajamento.Chave.REPRESENTACAO_TITULAR, 20)
        peso_presenca = PesoEngajamento.valor(PesoEngajamento.Chave.PRESENCA_ATIVIDADE, 5)
        meta_dinamica = max(
            sum(e.pontos_presencial for e in eventos_bienio) + peso_rep_titular + (peso_presenca * 4),
            50,
        )

        adimplencia = Adimplencia.objects.filter(
            municipio=self.municipio, ano_referencia=ano_atual,
        ).first()
        percentual = 0.0
        if adimplencia and adimplencia.status == Adimplencia.Status.INADIMPLENTE:
            percentual = float(config.penalidade_inadimplente)
        elif adimplencia and adimplencia.status == Adimplencia.Status.PARCIAL:
            percentual = float(config.penalidade_parcial)
        self.penalidade_adimplencia = int(self.pontuacao_bruta * percentual)

        liquida = self.pontuacao_bruta - self.penalidade_adimplencia
        self.pontuacao_normalizada = min(100, int((liquida / meta_dinamica) * 100))
        self.total_participacoes = total_itens

        if self.pontuacao_normalizada >= 70:
            self.nivel = self.Nivel.ALTO
        elif self.pontuacao_normalizada >= 40:
            self.nivel = self.Nivel.MEDIO
        elif self.pontuacao_normalizada >= 10:
            self.nivel = self.Nivel.BAIXO
        else:
            self.nivel = self.Nivel.INATIVO

        self.save()
