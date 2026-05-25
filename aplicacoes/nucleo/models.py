"""Models base do núcleo: ModeloBase (UUID + timestamps), Perfil de acesso e LogAlteracao."""

import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AtivosManager(models.Manager):
    """Manager que filtra registros arquivados (soft-deleted).

    Use ``Modelo.ativos.all()`` quando quiser apenas não-arquivados.
    O default ``Modelo.objects`` continua mostrando tudo para compatibilidade
    com queries antigas — sem isso, ``related_name`` e filtros existentes
    deixariam de enxergar dados.
    """

    def get_queryset(self):
        return super().get_queryset().filter(arquivado_em__isnull=True)


class ModeloBase(models.Model):
    """Modelo abstrato com UUID como PK, timestamps e soft delete opt-in."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    criado_em = models.DateTimeField('criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('atualizado em', auto_now=True)
    arquivado_em = models.DateTimeField(
        'arquivado em',
        null=True, blank=True,
        help_text='Marca de soft delete. Use arquivar() para esconder sem perder histórico.',
    )

    objects = models.Manager()
    ativos = AtivosManager()

    class Meta:
        abstract = True

    def arquivar(self, usuario=None):
        """Soft delete reversível — marca como arquivado e loga.

        Args:
            usuario: User que executou (opcional, mas recomendado).
        """
        from django.utils import timezone
        self.arquivado_em = timezone.now()
        self.save(update_fields=['arquivado_em', 'atualizado_em'])
        if usuario is not None:
            from aplicacoes.nucleo.servicos.auditoria import registrar_exclusao
            registrar_exclusao(usuario, self)

    def desarquivar(self):
        """Reverte soft delete."""
        self.arquivado_em = None
        self.save(update_fields=['arquivado_em', 'atualizado_em'])

    @property
    def arquivado(self):
        return self.arquivado_em is not None


class Perfil(models.Model):
    """Perfil de acesso vinculado 1:1 ao User Django.

    Combina:
    - ``tipo``: papel principal (visualizador, editor, admin) — mantido para
      retrocompatibilidade e como atalho para granular.
    - ``permissoes_extras``: lista de strings com permissões granulares
      adicionais (ex: ``pode_importar_ibge``, ``pode_editar_pesos``,
      ``pode_ver_dados_lgpd``). Permite escalar autorização sem migration.
    """

    # Permissoes conhecidas — usadas no admin (autocomplete) e validadas.
    PERMISSOES_DISPONIVEIS = [
        ('pode_editar', 'Editar dados (CRUD básico)'),
        ('pode_importar_ibge', 'Importar municípios do IBGE'),
        ('pode_editar_pesos', 'Editar pesos do engajamento'),
        ('pode_ver_dados_lgpd', 'Ver dados sensíveis (CPF, e-mail, telefone)'),
        ('pode_enviar_email_massa', 'Enviar mala direta'),
        ('pode_exportar', 'Exportar dados (CSV/Excel)'),
        ('pode_arquivar', 'Arquivar registros (soft delete)'),
    ]

    class TipoPerfil(models.TextChoices):
        VISUALIZADOR = 'visualizador', 'Visualizador'
        EDITOR = 'editor', 'Editor'
        ADMIN = 'admin', 'Administrador'
        PREFEITO = 'prefeito', 'Prefeito (portal externo)'
        EXTERNO = 'externo', 'Convidado externo (ACL por objeto)'

    class StatusAprovacao(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente de aprovação'
        APROVADO = 'aprovado', 'Aprovado'
        BLOQUEADO = 'bloqueado', 'Bloqueado'
        EXPIRADO = 'expirado', 'Expirado'

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
        verbose_name='usuario',
    )
    tipo = models.CharField(
        'tipo de perfil',
        max_length=15,
        choices=TipoPerfil.choices,
        default=TipoPerfil.VISUALIZADOR,
    )
    permissoes_extras = models.JSONField(
        'permissões extras',
        default=list,
        blank=True,
        help_text='Lista de slugs de permissão (ex: ["pode_importar_ibge", "pode_exportar"]).',
    )
    municipio_vinculado = models.ForeignKey(
        'cadastro.Municipio',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='perfis_vinculados',
        verbose_name='município vinculado',
        help_text='Para perfis tipo "prefeito": qual município ele(a) pode visualizar.',
    )
    municipios_visiveis = models.ManyToManyField(
        'cadastro.Municipio',
        blank=True,
        related_name='perfis_com_acesso',
        verbose_name='municípios visíveis (múltiplos)',
        help_text='Para perfis externos: lista de municípios que pode acessar além do vinculado.',
    )

    # Fluxo de aprovação (LGPD nível 2)
    status_aprovacao = models.CharField(
        'status de aprovação',
        max_length=15,
        choices=StatusAprovacao.choices,
        default=StatusAprovacao.APROVADO,
        help_text='Externos ficam PENDENTE até DPO/admin liberar.',
    )
    expira_em = models.DateField(
        'expira em',
        null=True, blank=True,
        help_text='Após esta data, o login é bloqueado automaticamente.',
    )
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='perfis_aprovados',
        verbose_name='aprovado por',
    )
    aprovado_em = models.DateTimeField('aprovado em', null=True, blank=True)
    justificativa_acesso = models.TextField(
        'justificativa do acesso', blank=True,
        help_text='Por que este usuário externo precisa acessar? Registrado para auditoria LGPD.',
    )
    requer_2fa = models.BooleanField(
        'requer 2FA?', default=False,
        help_text='Externos e admins devem ter 2FA habilitado.',
    )

    class Meta:
        verbose_name = 'perfil'
        verbose_name_plural = 'perfis'

    def __str__(self):
        return f'{self.usuario.get_full_name() or self.usuario.username} — {self.get_tipo_display()}'

    @property
    def eh_editor(self):
        """Retorna True se o perfil possui permissão de edição (tipo ou extra)."""
        if self.tipo in (self.TipoPerfil.EDITOR, self.TipoPerfil.ADMIN):
            return True
        return 'pode_editar' in (self.permissoes_extras or [])

    def pode(self, permissao):
        """Verifica se o perfil tem uma permissão granular específica.

        Admin sempre pode tudo. Editor herda permissões básicas de edição.
        """
        if self.tipo == self.TipoPerfil.ADMIN:
            return True
        if self.tipo == self.TipoPerfil.EDITOR and permissao in {
            'pode_editar', 'pode_exportar', 'pode_arquivar',
        }:
            return True
        return permissao in (self.permissoes_extras or [])

    @property
    def acesso_valido(self):
        """True se o perfil pode acessar agora — aprovado, não expirado, não bloqueado."""
        from django.utils import timezone
        if self.status_aprovacao != self.StatusAprovacao.APROVADO:
            return False
        if self.expira_em and self.expira_em < timezone.now().date():
            return False
        return True

    def expirar_se_necessario(self):
        """Marca como EXPIRADO se passou da data — idempotente."""
        from django.utils import timezone
        if (self.expira_em and self.expira_em < timezone.now().date()
                and self.status_aprovacao != self.StatusAprovacao.EXPIRADO):
            self.status_aprovacao = self.StatusAprovacao.EXPIRADO
            self.save(update_fields=['status_aprovacao'])


class FiltroSalvo(models.Model):
    """Atalho de filtros que o usuário salvou para reusar em uma lista.

    O ``escopo`` é o nome da URL Django da lista (ex.: ``cadastro:lista_municipios``)
    e ``parametros`` armazena a query string completa (ex.: ``regiao=sudeste&uf=SP``).
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='filtros_salvos',
        verbose_name='usuario',
    )
    escopo = models.CharField(
        'escopo (URL name)',
        max_length=100,
        help_text='Nome da URL da lista, ex. cadastro:lista_municipios.',
    )
    nome = models.CharField('nome', max_length=80)
    parametros = models.CharField(
        'parametros (query string)',
        max_length=500,
        help_text='Query string sem o "?" inicial.',
    )
    criado_em = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'filtro salvo'
        verbose_name_plural = 'filtros salvos'
        ordering = ['escopo', 'nome']
        unique_together = ['usuario', 'escopo', 'nome']
        indexes = [
            models.Index(fields=['usuario', 'escopo']),
        ]

    def __str__(self):
        return f'{self.usuario} — {self.escopo} — {self.nome}'


class WebhookSubscription(models.Model):
    """Assinatura externa para receber notificacoes de eventos do sistema.

    Cada subscricao registra uma URL HTTPS de destino + secret (HMAC) + lista
    de tipos de evento a receber. O dispatcher (em servicos/webhooks.py) envia
    POSTs assincronos quando os eventos ocorrem.

    Eventos disponiveis (slug):
        - municipio.adimplencia_mudou
        - evento.criado
        - atividade.realizada
        - missao.encerrada
        - pessoa.cadastrada

    Payload sempre contem: id, tipo, timestamp, dados.
    """

    nome = models.CharField('nome', max_length=80, help_text='Identificacao amigavel — ex: "PowerBI FNP".')
    url = models.URLField('URL de destino', help_text='Endpoint HTTPS que recebera os POSTs.')
    secret = models.CharField(
        'secret HMAC', max_length=64,
        help_text='Chave compartilhada — usada em X-FNP-Signature (HMAC-SHA256).',
    )
    eventos = models.JSONField(
        'eventos assinados', default=list,
        help_text='Lista de slugs. Vazio = nenhum (subscricao desativada).',
    )
    ativo = models.BooleanField('ativo?', default=True)
    criado_em = models.DateTimeField('criado em', auto_now_add=True)
    ultima_entrega = models.DateTimeField('ultima entrega', null=True, blank=True)
    ultima_falha = models.DateTimeField('ultima falha', null=True, blank=True)
    contador_falhas = models.IntegerField('falhas consecutivas', default=0)

    class Meta:
        verbose_name = 'webhook'
        verbose_name_plural = 'webhooks'

    def __str__(self):
        return f'{self.nome} → {self.url}'


class LogAlteracao(models.Model):
    """Registro imutável de auditoria — grava criação, edição e exclusão de objetos."""

    class TipoAcao(models.TextChoices):
        CRIACAO = 'criacao', 'Criacao'
        EDICAO = 'edicao', 'Edicao'
        EXCLUSAO = 'exclusao', 'Exclusao'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='logs_alteracao',
        verbose_name='usuario',
    )
    acao = models.CharField(
        'acao',
        max_length=10,
        choices=TipoAcao.choices,
    )
    modelo = models.CharField('modelo', max_length=100)
    objeto_id = models.CharField('ID do objeto', max_length=50)
    objeto_repr = models.CharField('representacao', max_length=255)
    campos_alterados = models.JSONField(
        'campos alterados',
        default=dict,
        blank=True,
        help_text='Dicionario com campo: {antes, depois}',
    )
    data = models.DateTimeField('data', auto_now_add=True)

    class Meta:
        verbose_name = 'log de alteracao'
        verbose_name_plural = 'logs de alteracao'
        ordering = ['-data']

    def __str__(self):
        return f'{self.usuario} — {self.get_acao_display()} — {self.modelo} — {self.objeto_repr}'


class AceiteTermo(models.Model):
    """Aceite do termo de uso + política de privacidade (LGPD Art. 8º).

    Registra quando cada usuário leu e aceitou os termos atuais — o
    middleware ``ExigirAceiteTermoMiddleware`` força o usuário sem aceite
    válido a passar pela tela ``/conta/termo-de-uso/`` antes de qualquer
    outra navegação. ``versao`` permite forçar re-aceite quando os termos
    forem revisados (incrementar VERSAO_ATUAL_TERMO em settings ou aqui).
    """

    # Incrementar quando os termos forem revisados — força re-aceite de todos.
    VERSAO_ATUAL = '2026-05'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='aceites_termo',
        verbose_name='usuario',
    )
    versao = models.CharField('versao do termo aceito', max_length=20)
    ip = models.GenericIPAddressField('IP no aceite', null=True, blank=True)
    user_agent = models.CharField('user agent', max_length=255, blank=True)
    aceito_em = models.DateTimeField('aceito em', auto_now_add=True)

    class Meta:
        verbose_name = 'aceite de termo'
        verbose_name_plural = 'aceites de termo'
        ordering = ['-aceito_em']
        unique_together = ['usuario', 'versao']
        indexes = [models.Index(fields=['usuario', '-aceito_em'])]

    def __str__(self):
        return f'{self.usuario} — termo {self.versao} aceito em {self.aceito_em:%d/%m/%Y %H:%M}'


class SolicitacaoExclusao(models.Model):
    """Pedido de exclusão de dados pelo titular (LGPD Art. 18, VI).

    A solicitação é registrada para auditoria — a exclusão efetiva é feita
    pelo DPO/admin via comando ``purgar_dados_antigos`` ou ação manual,
    preservando o rastro legal de quem pediu, quando e por quê.
    """

    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        EM_ANALISE = 'em_analise', 'Em analise'
        ATENDIDA = 'atendida', 'Atendida'
        NEGADA = 'negada', 'Negada (obrigacao legal de reter)'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='solicitacoes_exclusao',
        verbose_name='usuario solicitante',
    )
    email_contato = models.EmailField('e-mail de contato')
    motivo = models.TextField('motivo do pedido', blank=True)
    status = models.CharField(
        'status', max_length=15, choices=Status.choices, default=Status.PENDENTE,
    )
    resposta_dpo = models.TextField('resposta do DPO', blank=True)
    criado_em = models.DateTimeField('criado em', auto_now_add=True)
    atendido_em = models.DateTimeField('atendido em', null=True, blank=True)

    class Meta:
        verbose_name = 'solicitacao de exclusao (LGPD)'
        verbose_name_plural = 'solicitacoes de exclusao (LGPD)'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.email_contato} — {self.get_status_display()}'


class PermissaoEntidade(models.Model):
    """ACL por objeto — quem pode ver/editar uma entidade específica (LGPD nível 2).

    Permite que um usuário externo (ex: prefeito convidado) veja apenas o
    Evento X, a Missão Y e o Município Z para os quais foi convidado, sem
    enxergar nada mais. Combinado com ``Perfil.municipios_visiveis``, dá
    granularidade fina sem inflar o modelo Perfil com flags hardcoded.

    Convenção de uso:
    - ``perfil`` + ``content_type`` + ``object_id`` é único
    - ``nivel='visualizar'`` é o padrão (leitura); ``'editar'`` permite update
    - ``concedido_por`` registra quem deu o acesso (auditoria LGPD)
    """

    class Nivel(models.TextChoices):
        VISUALIZAR = 'visualizar', 'Visualizar'
        EDITAR = 'editar', 'Editar'

    perfil = models.ForeignKey(
        'Perfil', on_delete=models.CASCADE,
        related_name='permissoes_entidade',
        verbose_name='perfil',
    )
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE,
        verbose_name='tipo da entidade',
    )
    object_id = models.UUIDField('id do objeto')
    entidade = GenericForeignKey('content_type', 'object_id')
    nivel = models.CharField(
        'nível', max_length=12, choices=Nivel.choices, default=Nivel.VISUALIZAR,
    )
    concedido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='permissoes_concedidas',
        verbose_name='concedido por',
    )
    concedido_em = models.DateTimeField('concedido em', auto_now_add=True)
    expira_em = models.DateField(
        'expira em', null=True, blank=True,
        help_text='Acesso temporário a esta entidade. Vazio = sem expiração.',
    )
    justificativa = models.TextField('justificativa', blank=True)

    class Meta:
        verbose_name = 'permissão por entidade'
        verbose_name_plural = 'permissões por entidade'
        unique_together = ['perfil', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['perfil', 'content_type']),
        ]

    def __str__(self):
        return f'{self.perfil.usuario} → {self.entidade} ({self.get_nivel_display()})'


class LogAcessoSensivel(models.Model):
    """Registra LEITURA de dados sensíveis para auditoria LGPD (Art. 37, 46).

    Não é o mesmo que ``LogAlteracao`` (que rastreia CRUD). Aqui gravamos
    *quem viu o quê* — informação obrigatória para responder à ANPD em
    caso de incidente ou para investigar acesso suspeito (ex: usuário
    consultando 500 pessoas em 10 minutos = exfiltração).

    Aplicado via decorator ``@registrar_leitura_sensivel`` em views de
    detalhe de Pessoa, Visita e CredenciamentoPrevio.
    """

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True,
        related_name='logs_acesso_sensivel',
        verbose_name='usuário',
    )
    modelo = models.CharField('modelo acessado', max_length=80)
    objeto_id = models.CharField('id do objeto', max_length=50)
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.CharField('user agent', max_length=255, blank=True)
    contexto = models.CharField(
        'contexto', max_length=50, blank=True,
        help_text='Ex: "detalhe_pessoa", "exportacao_csv".',
    )
    data = models.DateTimeField('data', auto_now_add=True)

    class Meta:
        verbose_name = 'log de acesso sensível (LGPD)'
        verbose_name_plural = 'logs de acesso sensível (LGPD)'
        ordering = ['-data']
        indexes = [
            models.Index(fields=['usuario', '-data']),
            models.Index(fields=['modelo', 'objeto_id']),
            models.Index(fields=['-data']),
        ]

    def __str__(self):
        return f'{self.usuario} viu {self.modelo}#{self.objeto_id} em {self.data:%d/%m %H:%M}'
