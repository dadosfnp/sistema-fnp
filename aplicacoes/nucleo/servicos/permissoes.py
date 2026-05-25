"""Helpers de permissão centralizados — incluindo ACL por objeto (LGPD nível 2).

Funções principais:
- ``eh_editor`` / ``pode``: checagens herdadas (perfil + permissão granular)
- ``pode_ver(user, obj)``: ACL por entidade — usa PermissaoEntidade + escopo
  de município para decidir se um usuário pode ler um objeto específico
- ``filtrar_visiveis(user, queryset)``: limita um queryset aos objetos
  visíveis pelo usuário
"""

from django.contrib.contenttypes.models import ContentType


def eh_editor(request):
    """Compatível com o ``_eh_editor`` antigo — True se pode editar."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.perfil.eh_editor
    except Exception:
        return False


def pode(request, permissao):
    """Granular: verifica permissão específica (ex: 'pode_importar_ibge')."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        return user.perfil.pode(permissao)
    except Exception:
        return False


def _perfil_de(user):
    """Retorna o Perfil do usuário ou None — não levanta exceção."""
    if not user or not user.is_authenticated:
        return None
    return getattr(user, 'perfil', None)


def pode_ver(user, obj):
    """Decide se ``user`` pode visualizar o objeto ``obj`` (ACL por entidade).

    Hierarquia de decisão:
    1. Superuser ou admin → sempre
    2. Editor/visualizador interno (FNP) → sempre, exceto se perfil inválido
    3. Prefeito (portal) → só objetos do município vinculado
    4. Externo → precisa de PermissaoEntidade explícita OU o objeto deve
       pertencer a um município em ``municipios_visiveis``

    Args:
        user: ``request.user``
        obj: instância de qualquer model (Evento, Missao, Municipio, Pessoa…)

    Returns:
        bool — True se pode visualizar.
    """
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    perfil = _perfil_de(user)
    if not perfil or not perfil.acesso_valido:
        return False

    # Internos veem tudo (admin, editor, visualizador)
    if perfil.tipo in (
        perfil.TipoPerfil.ADMIN,
        perfil.TipoPerfil.EDITOR,
        perfil.TipoPerfil.VISUALIZADOR,
    ):
        return True

    # Municipio: prefeito do portal só vê o vinculado; externo, lista_visiveis
    from aplicacoes.cadastro.models import Municipio
    if isinstance(obj, Municipio):
        if perfil.tipo == perfil.TipoPerfil.PREFEITO:
            return perfil.municipio_vinculado_id == obj.id
        # Externo
        if perfil.municipio_vinculado_id == obj.id:
            return True
        return perfil.municipios_visiveis.filter(id=obj.id).exists()

    # Para objetos que TÊM município (ex: Pessoa via vínculo, Missao via cidade)
    municipio_do_obj = _municipio_de(obj)
    if municipio_do_obj is not None:
        if perfil.tipo == perfil.TipoPerfil.PREFEITO:
            return perfil.municipio_vinculado_id == municipio_do_obj.id
        # Externo: município está na sua lista?
        if perfil.municipio_vinculado_id == municipio_do_obj.id:
            return True
        if perfil.municipios_visiveis.filter(id=municipio_do_obj.id).exists():
            return True

    # Fallback: ACL explícita via PermissaoEntidade
    from aplicacoes.nucleo.models import PermissaoEntidade
    ct = ContentType.objects.get_for_model(obj.__class__)
    return PermissaoEntidade.objects.filter(
        perfil=perfil, content_type=ct, object_id=obj.pk,
    ).exists()


def _municipio_de(obj):
    """Extrai o município de uma entidade — heurística que cobre os principais models.

    Por que: muitas entidades têm vínculo natural com um município (Pessoa via
    VinculoMunicipio, Missao via município de origem). Centralizar aqui evita
    duplicar lógica em cada view.
    """
    municipio = getattr(obj, 'municipio', None)
    if municipio is not None:
        return municipio
    # Pessoa: usa vínculo vigente
    if obj.__class__.__name__ == 'Pessoa':
        try:
            vinculo = obj.vinculos.filter(vigente=True).first()
            return vinculo.municipio if vinculo else None
        except Exception:
            return None
    return None


def filtrar_visiveis(user, queryset):
    """Filtra um queryset deixando só os objetos que ``user`` pode ver.

    Implementação pragmática: itera o queryset chamando ``pode_ver``. Para
    listas grandes (>500), evite — use filtros nativos (``filter(municipio__in=...)``).
    Aqui priorizamos correção sobre performance: a maioria das telas de
    detalhe usa querysets já filtrados por contexto.
    """
    if not user or not user.is_authenticated:
        return queryset.none()
    if user.is_superuser:
        return queryset
    perfil = _perfil_de(user)
    if not perfil or not perfil.acesso_valido:
        return queryset.none()
    if perfil.tipo in (
        perfil.TipoPerfil.ADMIN,
        perfil.TipoPerfil.EDITOR,
        perfil.TipoPerfil.VISUALIZADOR,
    ):
        return queryset
    visiveis_ids = [obj.pk for obj in queryset if pode_ver(user, obj)]
    return queryset.filter(pk__in=visiveis_ids)


def conceder_acesso(perfil, obj, concedido_por, nivel='visualizar', expira_em=None, justificativa=''):
    """Helper para criar/atualizar uma PermissaoEntidade.

    Centraliza a operação para que o admin/DPO sempre registre quem
    concedeu o acesso e por quê — exigido para auditoria LGPD.
    """
    from aplicacoes.nucleo.models import PermissaoEntidade
    ct = ContentType.objects.get_for_model(obj.__class__)
    permissao, _ = PermissaoEntidade.objects.update_or_create(
        perfil=perfil, content_type=ct, object_id=obj.pk,
        defaults={
            'nivel': nivel,
            'concedido_por': concedido_por,
            'expira_em': expira_em,
            'justificativa': justificativa[:2000],
        },
    )
    return permissao
