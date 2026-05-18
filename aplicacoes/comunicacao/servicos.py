"""Serviços de Comunicação — coleta de destinatários e disparo de e-mails.

Centraliza a lógica de descobrir quem deve receber um e-mail relacionado a
uma entidade. A regra varia conforme a categoria:

- **Instância** → representantes vigentes
- **Atividade** → representantes vigentes da instância associada
- **Evento** → pessoas com participação confirmada
- **Missão** → membros da delegação
- **Projeto** → responsável (apenas)

Cada destinatário é uma tupla ``(pessoa, email, municipio)``.
"""

from django.contrib.contenttypes.models import ContentType

from aplicacoes.cadastro.models import Pessoa


def coletar_destinatarios(entidade):
    """Retorna lista de tuplas ``(pessoa, email, municipio_ou_none)`` para a entidade.

    Args:
        entidade: Instância de qualquer um dos models de categoria.

    Returns:
        Lista de dicts com chaves ``pessoa``, ``email``, ``municipio``.
        Apenas pessoas com e-mail cadastrado são incluídas.
    """
    from aplicacoes.atividades.models import Atividade
    from aplicacoes.eventos.models import Evento
    from aplicacoes.instancias.models import Instancia
    from aplicacoes.missoes.models import Missao
    from aplicacoes.projetos.models import Projeto

    pessoas_qs = Pessoa.objects.none()

    if isinstance(entidade, Instancia):
        pessoas_qs = Pessoa.objects.filter(
            representacoes__instancia=entidade,
            representacoes__vigente=True,
            ativo=True,
        ).distinct()
    elif isinstance(entidade, Atividade):
        pessoas_qs = Pessoa.objects.filter(
            representacoes__instancia=entidade.instancia,
            representacoes__vigente=True,
            ativo=True,
        ).distinct()
    elif isinstance(entidade, Evento):
        pessoas_qs = Pessoa.objects.filter(
            participacoes__evento=entidade,
            participacoes__confirmado=True,
            ativo=True,
        ).distinct()
    elif isinstance(entidade, Missao):
        pessoas_qs = Pessoa.objects.filter(
            participacoes_missao__missao=entidade,
            ativo=True,
        ).distinct()
    elif isinstance(entidade, Projeto):
        if entidade.responsavel:
            pessoas_qs = Pessoa.objects.filter(pk=entidade.responsavel_id)

    destinatarios = []
    for pessoa in pessoas_qs.order_by('nome'):
        if not pessoa.email:
            continue
        vinculo = pessoa.vinculos.filter(vigente=True).select_related('municipio').first()
        destinatarios.append({
            'pessoa': pessoa,
            'email': pessoa.email,
            'municipio': vinculo.municipio if vinculo else None,
        })
    return destinatarios


def categoria_para_entidade(entidade):
    """Mapeia uma entidade ao código de categoria correspondente no TemplateEmail."""
    from aplicacoes.atividades.models import Atividade
    from aplicacoes.comunicacao.models import TemplateEmail
    from aplicacoes.eventos.models import Evento
    from aplicacoes.instancias.models import Instancia
    from aplicacoes.missoes.models import Missao
    from aplicacoes.projetos.models import Projeto

    mapa = {
        Instancia: TemplateEmail.Categoria.INSTANCIAS,
        Projeto: TemplateEmail.Categoria.PROJETOS,
        Missao: TemplateEmail.Categoria.MISSOES,
        Atividade: TemplateEmail.Categoria.ATIVIDADES,
        Evento: TemplateEmail.Categoria.EVENTOS,
    }
    return mapa.get(type(entidade), TemplateEmail.Categoria.GERAL)
