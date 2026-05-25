"""Model de Presença universal — anexável a qualquer entidade via GenericForeignKey.

Permite registrar quem participou (ou faltou) em Atividades, Eventos, Missões
ou qualquer outra entidade que faça sentido controlar presença. O município é
gravado como snapshot na hora do registro — preserva o vínculo da pessoa ao
município mesmo que ela mude de cargo posteriormente.

Convive com ``eventos.Participacao`` (que mantém pontuação de engajamento) e
``missoes.MembroDelegacao`` (que detalha papéis na delegação) — não os
substitui, complementa: representa o ato simples de "presença".
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.nucleo.models import ModeloBase
from aplicacoes.nucleo.validators import validar_imagem_segura


class Presenca(ModeloBase):
    """Registro de presença/ausência de uma pessoa em uma entidade qualquer.

    O par ``content_type`` + ``object_id`` aponta para a entidade onde a
    presença ocorreu (Atividade, Evento, Missão etc.). ``municipio`` é um
    snapshot no momento do registro — não muda se o vínculo da pessoa
    posteriormente trocar.
    """

    class Status(models.TextChoices):
        PRESENTE = 'presente', 'Presente'
        AUSENTE = 'ausente', 'Ausente'
        JUSTIFICADA = 'justificada', 'Falta justificada'
        EM_TRANSITO = 'em_transito', 'Em trânsito / parcial'

    class Forma(models.TextChoices):
        PRESENCIAL = 'presencial', 'Presencial'
        ONLINE = 'online', 'Online'
        HIBRIDO = 'hibrido', 'Híbrido'

    pessoa = models.ForeignKey(
        Pessoa,
        on_delete=models.CASCADE,
        related_name='presencas',
        verbose_name='pessoa',
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='tipo da entidade',
    )
    object_id = models.UUIDField('id do objeto')
    entidade = GenericForeignKey('content_type', 'object_id')

    status = models.CharField(
        'status',
        max_length=15,
        choices=Status.choices,
        default=Status.PRESENTE,
    )
    forma = models.CharField(
        'forma de participação',
        max_length=12,
        choices=Forma.choices,
        default=Forma.PRESENCIAL,
    )
    municipio = models.ForeignKey(
        Municipio,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presencas',
        verbose_name='município (snapshot)',
        help_text='Município vinculado à pessoa no momento do registro.',
    )
    observacao = models.TextField('observação', blank=True)
    registrado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presencas_registradas',
        verbose_name='registrado por',
    )

    class Meta:
        verbose_name = 'presença'
        verbose_name_plural = 'presenças'
        ordering = ['-criado_em']
        unique_together = ['pessoa', 'content_type', 'object_id']
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return f'{self.pessoa} — {self.get_status_display()} em {self.entidade}'

    def save(self, *args, **kwargs):
        """Captura snapshot do município vigente da pessoa se ainda não preenchido."""
        if not self.municipio_id and self.pessoa_id:
            vinculo = self.pessoa.vinculos.filter(vigente=True).first()
            if vinculo:
                self.municipio = vinculo.municipio
        super().save(*args, **kwargs)


class Visita(ModeloBase):
    """Visita à sede da FNP registrada pela recepção/secretaria.

    Captura o fluxo simples de "alguém chegou aqui agora" — útil para:
    - Atendimento na recepção (cadastro rápido de quem chega)
    - Histórico de quem passou pela FNP em data X
    - Métrica de visitantes por dia/semana/mês
    - Cruzamento com eventos do dia (se houver)

    Diferente de ``Presenca`` (que aponta para uma entidade específica via
    GenericForeignKey), uma Visita é autônoma — basta nome + horário para
    registrar. Pode opcionalmente referenciar uma pessoa cadastrada e o
    evento/atividade que motivou a visita.
    """

    class Motivo(models.TextChoices):
        REUNIAO = 'reuniao', 'Reunião agendada'
        EVENTO = 'evento', 'Participar de evento/atividade'
        ENTREGA = 'entrega', 'Entrega de documento'
        TECNICO = 'tecnico', 'Atendimento técnico'
        VISITA_INSTITUCIONAL = 'institucional', 'Visita institucional'
        OUTRO = 'outro', 'Outro'

    # Pessoa cadastrada (opcional — se já existe, link; senão captura nome livre)
    pessoa = models.ForeignKey(
        Pessoa, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='visitas',
        help_text='Vincular a uma pessoa cadastrada se já existir.',
    )
    nome_visitante = models.CharField(
        'nome do visitante', max_length=255,
        help_text='Preenchido manualmente quando o visitante não tem cadastro.',
    )
    email = models.EmailField('e-mail', blank=True)
    telefone = models.CharField('telefone', max_length=20, blank=True)
    organizacao = models.CharField(
        'organização/cargo', max_length=255, blank=True,
        help_text='Empresa, prefeitura, secretaria etc.',
    )

    motivo = models.CharField(
        'motivo', max_length=20, choices=Motivo.choices, default=Motivo.OUTRO,
    )
    pessoa_recebida_por = models.CharField(
        'recebido(a) por', max_length=255, blank=True,
        help_text='Quem na FNP irá atender (livre — ex.: "Eq. Presidência").',
    )
    observacao = models.TextField('observação', blank=True)

    # Snapshot do município, se houver
    municipio = models.ForeignKey(
        Municipio, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='visitas',
        help_text='Município que o visitante representa (se aplicável).',
    )

    chegou_em = models.DateTimeField('chegou em', auto_now_add=True)
    saiu_em = models.DateTimeField('saiu em', null=True, blank=True)
    registrado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='visitas_registradas',
    )
    # Foto de credenciamento — capturada via webcam no momento do check-in
    # ou pré-enviada pelo visitante via link.
    foto = models.ImageField(
        'foto de credenciamento',
        upload_to='visitas/%Y/%m/',
        blank=True, null=True,
        validators=[validar_imagem_segura],
        help_text='Foto da pessoa visitando (webcam local ou enviada via pré-credenciamento).',
    )
    pre_credenciado = models.BooleanField(
        'veio pré-credenciado?', default=False,
        help_text='True se a foto/dados vieram de um link enviado antes da visita.',
    )
    face_embedding = models.JSONField(
        'embedding facial (face-api.js)', default=list, blank=True,
        help_text='Vetor de 128 floats extraído da foto via face-api.js para reconhecimento.',
    )

    class Meta:
        verbose_name = 'visita à FNP'
        verbose_name_plural = 'visitas à FNP'
        ordering = ['-chegou_em']
        indexes = [
            models.Index(fields=['-chegou_em']),
            models.Index(fields=['pessoa']),
        ]

    def __str__(self):
        return f'{self.nome_visitante} — {self.chegou_em:%d/%m/%Y %H:%M}'

    @property
    def ainda_presente(self):
        """True se o visitante ainda não foi registrado como saído."""
        return self.saiu_em is None

    def registrar_saida(self):
        """Marca a saída agora."""
        from django.utils import timezone
        self.saiu_em = timezone.now()
        self.save(update_fields=['saiu_em', 'atualizado_em'])


class CredenciamentoPrevio(ModeloBase):
    """Pré-credenciamento enviado por link público — preenche dados e foto antes da visita.

    Fluxo:
    1. Secretária clica em "Enviar pré-credenciamento" e informa nome + telefone/email.
    2. Sistema gera token único e URL pública /recepcao/pre/<token>/
    3. Link é enviado por WhatsApp/e-mail.
    4. Visitante abre o link no celular, tira foto, confirma dados.
    5. Quando chega na sede, secretária vê o pré-credenciamento "Pronto"
       e basta confirmar a entrada — Visita já tem foto e dados.

    Reduz fila no dia do evento e melhora a identificação visual da pessoa.
    """

    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente (link enviado)'
        PREENCHIDO = 'preenchido', 'Preenchido (aguardando chegada)'
        UTILIZADO = 'utilizado', 'Utilizado (visitou)'
        EXPIRADO = 'expirado', 'Expirado'

    token = models.CharField(
        'token publico', max_length=64, unique=True,
        help_text='Slug aleatorio usado na URL publica. Expira em 30 dias.',
    )
    nome_visitante = models.CharField('nome do visitante', max_length=255)
    telefone = models.CharField('telefone (WhatsApp)', max_length=20, blank=True)
    email = models.EmailField('e-mail', blank=True)
    cpf = models.CharField(
        'CPF', max_length=14, blank=True,
        help_text='Opcional. Apenas dígitos ou formato XXX.XXX.XXX-XX.',
    )
    rg = models.CharField(
        'RG', max_length=20, blank=True,
        help_text='Opcional. Útil quando o visitante não tem CPF à mão.',
    )
    organizacao = models.CharField('organização/cargo', max_length=255, blank=True)
    motivo = models.CharField('motivo da visita', max_length=255, blank=True)
    data_visita_prevista = models.DateField('data prevista da visita', null=True, blank=True)

    # Preenchido pelo proprio visitante via link publico
    foto = models.ImageField(
        'foto enviada pelo visitante',
        upload_to='credenciamentos/%Y/%m/',
        blank=True, null=True,
        validators=[validar_imagem_segura],
    )
    documentos_aceitos = models.BooleanField(
        'aceitou termos LGPD?',
        default=False,
        help_text='Aceite do tratamento de imagem para credenciamento.',
    )
    face_embedding = models.JSONField(
        'embedding facial (face-api.js)', default=list, blank=True,
        help_text='Vetor de 128 floats extraído da foto enviada pelo visitante.',
    )

    status = models.CharField(
        'status', max_length=12, choices=Status.choices, default=Status.PENDENTE,
    )
    expira_em = models.DateTimeField('expira em')
    criado_por = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='credenciamentos_enviados',
    )
    visita_gerada = models.ForeignKey(
        'Visita', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='origem_pre_credenciamento',
    )
    # Entidade que originou o convite (opcional) — evento/atividade/missao/etc.
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
        verbose_name='tipo da entidade de origem',
    )
    object_id = models.UUIDField(
        'id do objeto de origem', null=True, blank=True,
        help_text='Vincula o pré-credenciamento ao evento/atividade/missão que motivou o convite.',
    )
    entidade_origem = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = 'pré-credenciamento'
        verbose_name_plural = 'pré-credenciamentos'
        ordering = ['-criado_em']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['status', '-criado_em']),
            models.Index(fields=['content_type', 'object_id']),
        ]

    def __str__(self):
        return f'{self.nome_visitante} ({self.get_status_display()})'

    @classmethod
    def gerar_token(cls):
        """Gera token URL-safe único de 32 caracteres."""
        import secrets
        return secrets.token_urlsafe(24)

    def url_publica(self, request=None):
        """Retorna a URL absoluta do link de pré-credenciamento."""
        from django.urls import reverse
        path = reverse('presenca:pre_credenciamento_publico', args=[self.token])
        if request:
            return request.build_absolute_uri(path)
        return path
