from aplicacoes.nucleo.models import LogAlteracao


def registrar_criacao(usuario, objeto):
    """Registra log de criacao de um objeto."""
    LogAlteracao.objects.create(
        usuario=usuario,
        acao=LogAlteracao.TipoAcao.CRIACAO,
        modelo=objeto.__class__.__name__,
        objeto_id=str(objeto.pk),
        objeto_repr=str(objeto)[:255],
    )


def registrar_edicao(usuario, objeto, campos_alterados):
    """Registra log de edicao com os campos que mudaram."""
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
    """Registra log de exclusao de um objeto."""
    LogAlteracao.objects.create(
        usuario=usuario,
        acao=LogAlteracao.TipoAcao.EXCLUSAO,
        modelo=objeto.__class__.__name__,
        objeto_id=str(objeto.pk),
        objeto_repr=str(objeto)[:255],
    )


def detectar_alteracoes(objeto, dados_novos):
    """Compara campos do objeto com dados novos e retorna dict de mudancas."""
    alteracoes = {}
    for campo, valor_novo in dados_novos.items():
        valor_atual = getattr(objeto, campo, None)
        if str(valor_atual) != str(valor_novo):
            alteracoes[campo] = {
                'antes': str(valor_atual),
                'depois': str(valor_novo),
            }
    return alteracoes
