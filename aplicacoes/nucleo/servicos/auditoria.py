"""Serviço de auditoria — funções para registrar criação, edição e exclusão de objetos.

O ``LogAlteracao`` (em ``aplicacoes.nucleo.models``) é um registro genérico
identificado por ``modelo`` (nome da classe) + ``objeto_id`` (PK como string).
Isso permite consultar o histórico de qualquer entidade do sistema sem precisar
de tabelas dedicadas por categoria — basta filtrar por esses dois campos.
"""

from aplicacoes.nucleo.models import LogAlteracao
from aplicacoes.nucleo.validators import mascarar_pii

# Campos que podem conter PII e devem ser mascarados em logs persistentes.
# Mantemos a chave (nome do campo) mas substituímos o valor por máscara.
_CAMPOS_PII = {
    'cpf', 'rg', 'email', 'telefone', 'celular', 'whatsapp',
    'endereco', 'cep', 'numero', 'complemento', 'nascimento', 'data_nascimento',
}


def _mascarar_alteracoes(campos_alterados):
    """Substitui valores de campos PII por máscara e roda mascarar_pii nos demais.

    Por que: LogAlteracao é uma tabela persistente consultável por vários
    perfis — guardar CPF/e-mail/telefone em claro viola LGPD Art. 6º (princípio
    da necessidade) e Art. 46 (medidas de segurança). Mascarar na entrada
    impede exposição mesmo se a query de log vazar.
    """
    if not campos_alterados:
        return campos_alterados
    saida = {}
    for campo, valores in campos_alterados.items():
        if campo in _CAMPOS_PII:
            saida[campo] = {'antes': '***', 'depois': '***'}
        elif isinstance(valores, dict):
            saida[campo] = {
                'antes': mascarar_pii(valores.get('antes', '')),
                'depois': mascarar_pii(valores.get('depois', '')),
            }
        else:
            saida[campo] = mascarar_pii(str(valores)) if valores is not None else valores
    return saida


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
        objeto_repr=mascarar_pii(str(objeto))[:255],
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
        objeto_repr=mascarar_pii(str(objeto))[:255],
        campos_alterados=_mascarar_alteracoes(campos_alterados),
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
        objeto_repr=mascarar_pii(str(objeto))[:255],
    )


def historico_de(objeto, limite=50):
    """Retorna o histórico de alterações de uma entidade qualquer.

    Args:
        objeto: Instância do model cuja história queremos consultar.
        limite: Número máximo de registros (mais recentes primeiro).

    Returns:
        QuerySet de ``LogAlteracao`` filtrado por modelo e PK do objeto.
    """
    return LogAlteracao.objects.filter(
        modelo=objeto.__class__.__name__,
        objeto_id=str(objeto.pk),
    ).select_related('usuario').order_by('-data')[:limite]


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
