"""Serviço de auditoria — funções para registrar criação, edição e exclusão de objetos."""

from aplicacoes.nucleo.models import LogAlteracao


def registrar_criacao(usuario, objeto):
    """Cria um LogAlteracao do tipo CRIACAO para o objeto informado.

    Args:
        usuario: User que realizou a ação.
        objeto: Instância do model criado.
    """
    LogAlteracao.objects.create(
        usuario=usuario,
        acao=LogAlteracao.TipoAcao.CRIACAO,
        modelo=objeto.__class__.__name__,
        objeto_id=str(objeto.pk),
        objeto_repr=str(objeto)[:255],
    )


def registrar_edicao(usuario, objeto, campos_alterados):
    """Cria um LogAlteracao do tipo EDICAO se houver campos alterados.

    Args:
        usuario: User que realizou a ação.
        objeto: Instância do model editado.
        campos_alterados: Dict ``{campo: {antes, depois}}`` retornado por ``detectar_alteracoes``.
    """
    if not campos_alterados:
        return
    LogAlteracao.objects.create(
        usuario=usuario,
        acao=LogAlteracao.TipoAcao.EDICAO,
        modelo=objeto.__class__.__name__,
        objeto_id=str(objeto.pk),
        objeto_repr=str(objeto)[:255],
        campos_alterados=campos_alterados,
    )


def registrar_exclusao(usuario, objeto):
    """Cria um LogAlteracao do tipo EXCLUSAO para o objeto informado.

    Args:
        usuario: User que realizou a ação.
        objeto: Instância do model excluído.
    """
    LogAlteracao.objects.create(
        usuario=usuario,
        acao=LogAlteracao.TipoAcao.EXCLUSAO,
        modelo=objeto.__class__.__name__,
        objeto_id=str(objeto.pk),
        objeto_repr=str(objeto)[:255],
    )


def detectar_alteracoes(objeto, dados_novos):
    """Compara valores atuais do objeto com dados novos (form.cleaned_data).

    Args:
        objeto: Instância do model antes da edição.
        dados_novos: Dict com os novos valores dos campos.

    Returns:
        Dict ``{campo: {'antes': str, 'depois': str}}`` apenas para campos modificados.
    """
    alteracoes = {}
    for campo, valor_novo in dados_novos.items():
        valor_atual = getattr(objeto, campo, None)
        if str(valor_atual) != str(valor_novo):
            alteracoes[campo] = {
                'antes': str(valor_atual),
                'depois': str(valor_novo),
            }
    return alteracoes
