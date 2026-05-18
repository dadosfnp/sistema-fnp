"""Views de Documentos — upload e exclusão associados a qualquer entidade.

Recebe ``app_label`` e ``model_name`` para identificar a entidade dona via
ContentType. Permissão restrita a editores.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404, redirect, render

from aplicacoes.documentos.forms import DocumentoForm
from aplicacoes.documentos.models import Documento
from aplicacoes.nucleo.servicos.auditoria import registrar_criacao, registrar_exclusao


def _eh_editor(request):
    """Retorna True se o usuário atual pode enviar/remover documentos."""
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.eh_editor
    except Exception:
        return False


def _resolver_entidade(app_label, model_name, object_id):
    """Resolve a entidade dona do documento via ContentType + object_id."""
    content_type = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    model_class = content_type.model_class()
    entidade = get_object_or_404(model_class, pk=object_id)
    return content_type, entidade


def _url_retorno(app_label, model_name, object_id):
    """Resolve a URL de retorno mais apropriada para a entidade.

    Por ora, redireciona para a listagem do app correspondente — quando cada
    app tiver uma view de detalhe dedicada, podemos refinar este mapeamento.
    """
    mapa_listas = {
        'instancias': 'instancias:lista_instancias',
        'projetos': 'projetos:lista_projetos',
        'missoes': 'missoes:lista_missoes',
        'atividades': 'atividades:lista_atividades',
        'eventos': 'eventos:lista_eventos',
    }
    return mapa_listas.get(app_label, 'nucleo:inicio')


@login_required
def documentos_da_entidade(request, app_label, model_name, object_id):
    """Lista os documentos de uma entidade específica com opção de upload."""
    content_type, entidade = _resolver_entidade(app_label, model_name, object_id)
    documentos = Documento.objects.filter(
        content_type=content_type, object_id=object_id,
    ).select_related('enviado_por')
    contexto = {
        'entidade': entidade,
        'documentos': documentos,
        'app_label': app_label,
        'model_name': model_name,
        'object_id': object_id,
        'eh_editor': _eh_editor(request),
        'url_retorno': _url_retorno(app_label, model_name, object_id),
    }
    return render(request, 'documentos/lista_documentos.html', contexto)


@login_required
def adicionar_documento(request, app_label, model_name, object_id):
    """Formulário de upload de documento para uma entidade qualquer."""
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para anexar documentos.')
        return redirect(_url_retorno(app_label, model_name, object_id))
    content_type, entidade = _resolver_entidade(app_label, model_name, object_id)
    if request.method == 'POST':
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            documento = form.save(commit=False)
            documento.content_type = content_type
            documento.object_id = object_id
            documento.enviado_por = request.user
            documento.save()
            registrar_criacao(request.user, documento)
            messages.success(request, f'Documento "{documento.nome}" anexado a {entidade}.')
            return redirect('documentos:listar', app_label=app_label, model_name=model_name, object_id=object_id)
    else:
        form = DocumentoForm()
    contexto = {
        'form': form,
        'entidade': entidade,
        'app_label': app_label,
        'model_name': model_name,
        'object_id': object_id,
    }
    return render(request, 'documentos/form_documento.html', contexto)


@login_required
def remover_documento(request, pk):
    """Remove um documento — restrito a editores."""
    documento = get_object_or_404(Documento, pk=pk)
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para remover documentos.')
        return redirect('nucleo:inicio')
    app_label = documento.content_type.app_label
    model_name = documento.content_type.model
    object_id = documento.object_id
    registrar_exclusao(request.user, documento)
    documento.delete()
    messages.success(request, 'Documento removido.')
    return redirect('documentos:listar', app_label=app_label, model_name=model_name, object_id=object_id)
