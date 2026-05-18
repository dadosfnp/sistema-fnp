"""Views de Presença — listagem, marcação em massa e check-in de visitantes."""

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from aplicacoes.cadastro.models import Municipio, Pessoa, VinculoMunicipio
from aplicacoes.instancias.models import Representacao
from aplicacoes.nucleo.servicos.auditoria import registrar_criacao
from aplicacoes.presenca.models import Presenca, Visita


def _eh_editor(request):
    """Retorna True se o usuário atual pode registrar presença."""
    if request.user.is_superuser:
        return True
    try:
        return request.user.perfil.eh_editor
    except Exception:
        return False


def _resolver_entidade(app_label, model_name, object_id):
    """Resolve a entidade alvo da presença via ContentType + object_id."""
    content_type = get_object_or_404(ContentType, app_label=app_label, model=model_name)
    model_class = content_type.model_class()
    entidade = get_object_or_404(model_class, pk=object_id)
    return content_type, entidade


def _candidatos_para(entidade):
    """Lista de Pessoas que fazem sentido pra marcar presença nesta entidade.

    - Atividade: representantes vigentes da instância
    - Outras entidades: todas as pessoas ativas (fallback)
    """
    from aplicacoes.atividades.models import Atividade
    if isinstance(entidade, Atividade):
        return Pessoa.objects.filter(
            representacoes__instancia=entidade.instancia,
            representacoes__vigente=True,
            ativo=True,
        ).distinct().order_by('nome')
    return Pessoa.objects.filter(ativo=True).order_by('nome')


def _url_retorno(app_label, model_name, object_id):
    """URL para a qual retornar depois de marcar presenças."""
    mapa = {
        ('atividades', 'atividade'): ('atividades:detalhe_atividade', {'pk': object_id}),
        ('eventos', 'evento'): ('eventos:detalhe_evento', {'pk': object_id}),
        ('missoes', 'missao'): ('missoes:detalhe_missao', {'pk': object_id}),
        ('instancias', 'instancia'): ('instancias:detalhe_instancia', {'pk': object_id}),
        ('projetos', 'projeto'): ('projetos:detalhe_projeto', {'pk': object_id}),
    }
    return mapa.get((app_label, model_name), ('nucleo:inicio', {}))


def _mapear_papel_vinculo(tipo_pessoa):
    """Mapeia ``Pessoa.tipo`` ao papel correspondente no ``VinculoMunicipio``."""
    mapa = {
        Pessoa.TipoPessoa.PREFEITO: VinculoMunicipio.Papel.PREFEITO,
        Pessoa.TipoPessoa.VICE_PREFEITO: VinculoMunicipio.Papel.VICE_PREFEITO,
        Pessoa.TipoPessoa.SECRETARIO: VinculoMunicipio.Papel.SECRETARIO,
        Pessoa.TipoPessoa.ASSESSOR: VinculoMunicipio.Papel.ASSESSOR,
        Pessoa.TipoPessoa.VEREADOR: VinculoMunicipio.Papel.VEREADOR,
    }
    return mapa.get(tipo_pessoa, VinculoMunicipio.Papel.CONTATO)


@login_required
def adicionar_pessoa_modal(request, app_label, model_name, object_id):
    """Modal HTMX para cadastrar pessoa nova durante a marcação de presença.

    Em GET, renderiza o formulário (campos mínimos + select de município).
    Em POST, cria Pessoa, vincula ao município, opcionalmente cria
    Representação quando a entidade-alvo é uma Atividade, e por fim marca
    presença. Retorna fragmento ``modal_pessoa_adicionada.html`` que
    dispara um reload da página de presença para atualizar a lista.
    """
    if not _eh_editor(request):
        return HttpResponse('Sem permissão.', status=403)

    content_type, entidade = _resolver_entidade(app_label, model_name, object_id)

    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip() or None
        telefone = request.POST.get('telefone', '').strip()
        tipo = request.POST.get('tipo', Pessoa.TipoPessoa.OUTRO)
        cargo = request.POST.get('cargo', '').strip()
        municipio_id = request.POST.get('municipio') or None
        status_presenca = request.POST.get('status', Presenca.Status.PRESENTE)
        forma_presenca = request.POST.get('forma', Presenca.Forma.PRESENCIAL)
        observacao = request.POST.get('observacao', '').strip()

        if not nome:
            return render(request, 'presenca/parciais/modal_adicionar_pessoa.html', {
                'app_label': app_label, 'model_name': model_name, 'object_id': object_id,
                'entidade': entidade,
                'municipios': Municipio.objects.order_by('nome'),
                'tipos': Pessoa.TipoPessoa.choices,
                'status_choices': Presenca.Status.choices,
                'forma_choices': Presenca.Forma.choices,
                'erro_form': 'Nome obrigatório.',
                'dados': request.POST,
            })

        municipio = Municipio.objects.filter(pk=municipio_id).first() if municipio_id else None

        pessoa = Pessoa.objects.create(
            nome=nome, email=email, telefone=telefone, tipo=tipo, cargo=cargo,
        )
        registrar_criacao(request.user, pessoa)

        if municipio:
            papel = _mapear_papel_vinculo(tipo)
            VinculoMunicipio.objects.create(
                pessoa=pessoa, municipio=municipio, papel=papel, vigente=True,
            )

        from aplicacoes.atividades.models import Atividade
        if isinstance(entidade, Atividade) and request.POST.get('criar_representacao') == 'on':
            Representacao.objects.create(
                instancia=entidade.instancia, pessoa=pessoa,
                funcao=Representacao.Funcao.PARTICIPANTE, vigente=True,
            )

        presenca = Presenca(
            pessoa=pessoa, content_type=content_type, object_id=object_id,
            status=status_presenca, forma=forma_presenca,
            municipio=municipio, observacao=observacao,
            registrado_por=request.user,
        )
        presenca.save()
        registrar_criacao(request.user, presenca)

        return render(request, 'presenca/parciais/modal_pessoa_adicionada.html', {
            'pessoa': pessoa, 'presenca': presenca,
        })

    return render(request, 'presenca/parciais/modal_adicionar_pessoa.html', {
        'app_label': app_label, 'model_name': model_name, 'object_id': object_id,
        'entidade': entidade,
        'municipios': Municipio.objects.order_by('nome'),
        'tipos': Pessoa.TipoPessoa.choices,
        'status_choices': Presenca.Status.choices,
        'forma_choices': Presenca.Forma.choices,
    })


@login_required
def marcar_presencas(request, app_label, model_name, object_id):
    """Formulário de marcação em massa de presença para uma entidade.

    Exibe a lista de candidatos (representantes da instância, no caso de
    Atividade) com selects de status/forma. Atualiza ou cria registros
    ``Presenca`` em massa.
    """
    if not _eh_editor(request):
        messages.error(request, 'Voce nao tem permissao para registrar presencas.')
        url, kwargs = _url_retorno(app_label, model_name, object_id)
        return redirect(url, **kwargs)

    content_type, entidade = _resolver_entidade(app_label, model_name, object_id)
    candidatos = _candidatos_para(entidade)
    presencas_existentes = {
        p.pessoa_id: p for p in Presenca.objects.filter(
            content_type=content_type, object_id=object_id,
        )
    }

    if request.method == 'POST':
        criados, atualizados = 0, 0
        for pessoa in candidatos:
            status = request.POST.get(f'status_{pessoa.pk}', '').strip()
            forma = request.POST.get(f'forma_{pessoa.pk}', '').strip() or Presenca.Forma.PRESENCIAL
            observacao = request.POST.get(f'observacao_{pessoa.pk}', '').strip()
            if not status:
                continue
            presenca = presencas_existentes.get(pessoa.pk)
            if presenca:
                presenca.status = status
                presenca.forma = forma
                presenca.observacao = observacao
                presenca.registrado_por = request.user
                presenca.save()
                atualizados += 1
            else:
                presenca = Presenca(
                    pessoa=pessoa,
                    content_type=content_type,
                    object_id=object_id,
                    status=status,
                    forma=forma,
                    observacao=observacao,
                    registrado_por=request.user,
                )
                presenca.save()
                registrar_criacao(request.user, presenca)
                criados += 1
        messages.success(
            request,
            f'Presencas registradas: {criados} novas, {atualizados} atualizadas.',
        )
        url, kwargs = _url_retorno(app_label, model_name, object_id)
        return redirect(url, **kwargs)

    # Monta linhas pra renderização com vínculo de município.
    linhas = []
    for pessoa in candidatos:
        vinculo = pessoa.vinculos.filter(vigente=True).select_related('municipio').first()
        existente = presencas_existentes.get(pessoa.pk)
        linhas.append({
            'pessoa': pessoa,
            'municipio': vinculo.municipio if vinculo else None,
            'presenca': existente,
        })

    contexto = {
        'entidade': entidade,
        'app_label': app_label,
        'model_name': model_name,
        'object_id': object_id,
        'linhas': linhas,
        'status_choices': Presenca.Status.choices,
        'forma_choices': Presenca.Forma.choices,
    }
    return render(request, 'presenca/form_marcar_presencas.html', contexto)


# ============================================================================
# RECEPCAO — check-in rapido de visitantes
# ============================================================================

@login_required
def recepcao(request):
    """Tela principal da recepcao: lista visitas do dia + botao de novo check-in.

    Otimizada para tablet/desktop da secretaria. Fontes grandes, cards visuais,
    botao de "Saiu" para registrar saida com 1 clique.
    """
    hoje = timezone.now().date()
    visitas_hoje = (
        Visita.objects.filter(chegou_em__date=hoje)
        .select_related('pessoa', 'municipio', 'registrado_por')
        .order_by('-chegou_em')
    )
    ainda_presentes = visitas_hoje.filter(saiu_em__isnull=True).count()
    return render(request, 'presenca/recepcao.html', {
        'visitas_hoje': visitas_hoje,
        'total_hoje': visitas_hoje.count(),
        'ainda_presentes': ainda_presentes,
        'data_hoje': hoje,
    })


@login_required
def recepcao_novo(request):
    """Formulario simples de check-in. Cria Visita e opcionalmente Pessoa."""
    if request.method == 'POST':
        nome = (request.POST.get('nome_visitante') or '').strip()
        if not nome:
            messages.error(request, 'Nome do visitante e obrigatorio.')
            return redirect('presenca:recepcao_novo')

        # Reusa Pessoa existente se informada (via pessoa_id) ou pesquisa por nome
        pessoa = None
        pessoa_id = request.POST.get('pessoa_id') or None
        if pessoa_id:
            pessoa = Pessoa.objects.filter(pk=pessoa_id).first()

        municipio_id = request.POST.get('municipio_id') or None
        municipio = Municipio.objects.filter(pk=municipio_id).first() if municipio_id else None

        visita = Visita.objects.create(
            pessoa=pessoa,
            nome_visitante=nome,
            email=(request.POST.get('email') or '').strip(),
            telefone=(request.POST.get('telefone') or '').strip(),
            organizacao=(request.POST.get('organizacao') or '').strip(),
            motivo=request.POST.get('motivo') or Visita.Motivo.OUTRO,
            pessoa_recebida_por=(request.POST.get('pessoa_recebida_por') or '').strip(),
            observacao=(request.POST.get('observacao') or '').strip(),
            municipio=municipio,
            registrado_por=request.user,
        )
        registrar_criacao(request.user, visita)
        messages.success(request, f'{nome} registrado(a) com sucesso.')
        return redirect('presenca:recepcao')

    # Lista de pessoas conhecidas e municipios pra autocomplete
    return render(request, 'presenca/recepcao_novo.html', {
        'motivos': Visita.Motivo.choices,
    })


@login_required
def recepcao_buscar_pessoa(request):
    """Endpoint JSON que pesquisa pessoas cadastradas por nome — autocomplete."""
    termo = (request.GET.get('q') or '').strip()
    if len(termo) < 2:
        return JsonResponse({'pessoas': []})
    pessoas = Pessoa.objects.filter(
        Q(nome__icontains=termo) | Q(email__icontains=termo)
    ).filter(ativo=True).select_related()[:8]
    out = []
    for p in pessoas:
        vinculo = p.vinculos.filter(vigente=True).select_related('municipio').first()
        out.append({
            'id': str(p.pk),
            'nome': p.nome,
            'email': p.email or '',
            'telefone': p.telefone or '',
            'cargo': p.cargo or p.get_tipo_display(),
            'municipio_id': str(vinculo.municipio.pk) if vinculo else '',
            'municipio_nome': f'{vinculo.municipio.nome}/{vinculo.municipio.uf}' if vinculo else '',
        })
    return JsonResponse({'pessoas': out})


@login_required
def recepcao_registrar_saida(request, pk):
    """Marca a saida do visitante (POST). Retorna fragmento HTMX atualizado."""
    if request.method != 'POST':
        return JsonResponse({'erro': 'use POST'}, status=405)
    visita = get_object_or_404(Visita, pk=pk)
    visita.registrar_saida()
    if request.headers.get('HX-Request'):
        return render(request, 'presenca/parciais/linha_visita.html', {'v': visita})
    return redirect('presenca:recepcao')


@login_required
def recepcao_historico(request):
    """Listagem com filtros para consultar visitas anteriores."""
    data_de = request.GET.get('de') or (timezone.now() - timedelta(days=7)).date().isoformat()
    data_ate = request.GET.get('ate') or timezone.now().date().isoformat()
    motivo = request.GET.get('motivo') or ''

    visitas = Visita.objects.select_related('pessoa', 'municipio')
    try:
        de = datetime.fromisoformat(data_de).date()
        ate = datetime.fromisoformat(data_ate).date()
        visitas = visitas.filter(chegou_em__date__gte=de, chegou_em__date__lte=ate)
    except ValueError:
        pass
    if motivo:
        visitas = visitas.filter(motivo=motivo)
    visitas = visitas.order_by('-chegou_em')[:200]

    return render(request, 'presenca/recepcao_historico.html', {
        'visitas': visitas,
        'data_de': data_de,
        'data_ate': data_ate,
        'motivo': motivo,
        'motivos': Visita.Motivo.choices,
    })
