from django.db import models
from django.utils import timezone

from aplicacoes.cadastro.models import Municipio
from aplicacoes.nucleo.models import ModeloBase


class ConfiguracaoEngajamento(ModeloBase):
    """Configurações globais do sistema de engajamento."""

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
        # Singleton: garante que só existe uma configuração
        self.pk = self.pk or ConfiguracaoEngajamento.objects.first() and ConfiguracaoEngajamento.objects.first().pk
        super().save(*args, **kwargs)

    @classmethod
    def atual(cls):
        obj, _ = cls.objects.get_or_create(
            pk=cls.objects.first().pk if cls.objects.exists() else None,
            defaults={'bienio_atual': '2025-2026'},
        )
        return obj


class Engajamento(ModeloBase):
    """Pontuação de engajamento de um município no biênio."""

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
        """Recalcula a pontuação relativa aos eventos cadastrados no biênio.

        A meta é dinâmica: soma dos pontos_presencial de todos os eventos
        do biênio. Se existem 3 eventos valendo 10 pts cada, a meta é 30.
        Um município que participou de todos presencialmente terá 100/100.
        """
        from aplicacoes.adimplencia.models import Adimplencia
        from aplicacoes.eventos.models import Evento, Participacao

        config = ConfiguracaoEngajamento.atual()
        anos = self.bienio.split('-')
        ano1, ano2 = int(anos[0]), int(anos[1])
        ano_atual = timezone.now().year

        # Eventos cadastrados no biênio
        eventos_bienio = Evento.objects.filter(
            data_inicio__year__in=[ano1, ano2],
        )

        # Meta dinâmica: soma dos pontos presenciais de todos os eventos
        meta_dinamica = sum(e.pontos_presencial for e in eventos_bienio)

        # Participações confirmadas deste município
        participacoes = Participacao.objects.filter(
            municipio=self.municipio,
            confirmado=True,
            evento__data_inicio__year__in=[ano1, ano2],
        )

        pontos_ano1 = sum(
            p.pontos_calculados
            for p in participacoes.filter(evento__data_inicio__year=ano1)
        )
        pontos_ano2 = sum(
            p.pontos_calculados
            for p in participacoes.filter(evento__data_inicio__year=ano2)
        )

        # Decaimento: ano anterior perde pontos se estamos no ano 2
        if ano_atual >= ano2:
            self.pontuacao_ano_anterior = pontos_ano1
            self.pontuacao_ano_atual = pontos_ano2
            self.pontuacao_bruta = int(
                pontos_ano2 + (pontos_ano1 * float(config.fator_decaimento))
            )
        else:
            self.pontuacao_ano_anterior = 0
            self.pontuacao_ano_atual = pontos_ano1
            self.pontuacao_bruta = pontos_ano1

        # Penalidade por adimplência
        adimplencia = Adimplencia.objects.filter(
            municipio=self.municipio,
            ano_referencia=ano_atual,
        ).first()

        percentual_penalidade = 0
        if adimplencia:
            if adimplencia.status == Adimplencia.Status.INADIMPLENTE:
                percentual_penalidade = float(config.penalidade_inadimplente)
            elif adimplencia.status == Adimplencia.Status.PARCIAL:
                percentual_penalidade = float(config.penalidade_parcial)

        self.penalidade_adimplencia = int(self.pontuacao_bruta * percentual_penalidade)
        pontuacao_liquida = self.pontuacao_bruta - self.penalidade_adimplencia

        # Normalizar para 0-100 usando meta dinâmica (eventos cadastrados)
        if meta_dinamica > 0:
            self.pontuacao_normalizada = min(100, int((pontuacao_liquida / meta_dinamica) * 100))
        else:
            self.pontuacao_normalizada = 0

        # Total de participações
        self.total_participacoes = participacoes.count()

        # Nível
        if self.pontuacao_normalizada >= 70:
            self.nivel = self.Nivel.ALTO
        elif self.pontuacao_normalizada >= 40:
            self.nivel = self.Nivel.MEDIO
        elif self.pontuacao_normalizada >= 10:
            self.nivel = self.Nivel.BAIXO
        else:
            self.nivel = self.Nivel.INATIVO

        self.save()
