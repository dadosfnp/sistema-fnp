"""Views de relatórios — dashboard com gráficos e exportação Excel/PDF."""

import json
from collections import defaultdict
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import HttpResponse
from django.shortcuts import render

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.engajamento.models import Engajamento
from aplicacoes.eventos.models import Evento, Participacao


def _dados_dashboard():
    """Coleta dados agregados para gráficos do painel."""
    # Adimplência por status (ano mais recente)
    ano_mais_recente = Adimplencia.objects.order_by('-ano_referencia').values_list('ano_referencia', flat=True).first() or 2026
    adimplencia_status = dict(
        Adimplencia.objects.filter(ano_referencia=ano_mais_recente)
        .values_list('status')
        .annotate(total=Count('id'))
        .values_list('status', 'total')
    )

    # Engajamento por nível
    engajamento_niveis = dict(
        Engajamento.objects.values_list('nivel').annotate(total=Count('id')).values_list('nivel', 'total')
    )

    # Municípios por região
    municipios_regiao = dict(
        Municipio.objects.values_list('regiao').annotate(total=Count('id')).values_list('regiao', 'total')
    )

    # Participações por tipo de evento
    part_por_tipo = dict(
        Participacao.objects.filter(confirmado=True)
        .values_list('evento__tipo')
        .annotate(total=Count('id'))
        .values_list('evento__tipo', 'total')
    )

    # Pessoas por tipo
    pessoas_tipo = dict(
        Pessoa.objects.filter(ativo=True)
        .values_list('tipo')
        .annotate(total=Count('id'))
        .values_list('tipo', 'total')
    )

    return {
        'ano_adimplencia': ano_mais_recente,
        'adimplencia_status': adimplencia_status,
        'engajamento_niveis': engajamento_niveis,
        'municipios_regiao': municipios_regiao,
        'part_por_tipo': part_por_tipo,
        'pessoas_tipo': pessoas_tipo,
    }


@login_required
def painel(request):
    """Renderiza o dashboard de relatórios com dados para Chart.js."""
    dados = _dados_dashboard()
    ctx = {
        # JSON para Chart.js
        'adimplencia_json': json.dumps({
            'labels': ['Adimplente', 'Inadimplente', 'Parcial'],
            'data': [
                dados['adimplencia_status'].get('adimplente', 0),
                dados['adimplencia_status'].get('inadimplente', 0),
                dados['adimplencia_status'].get('parcial', 0),
            ],
        }),
        'engajamento_json': json.dumps({
            'labels': ['Alto', 'Medio', 'Baixo', 'Inativo'],
            'data': [
                dados['engajamento_niveis'].get('alto', 0),
                dados['engajamento_niveis'].get('medio', 0),
                dados['engajamento_niveis'].get('baixo', 0),
                dados['engajamento_niveis'].get('inativo', 0),
            ],
        }),
        'regioes_json': json.dumps({
            'labels': ['Norte', 'Nordeste', 'Centro-Oeste', 'Sudeste', 'Sul'],
            'data': [
                dados['municipios_regiao'].get('norte', 0),
                dados['municipios_regiao'].get('nordeste', 0),
                dados['municipios_regiao'].get('centro_oeste', 0),
                dados['municipios_regiao'].get('sudeste', 0),
                dados['municipios_regiao'].get('sul', 0),
            ],
        }),
        'ano_adimplencia': dados['ano_adimplencia'],
        'total_pessoas': Pessoa.objects.filter(ativo=True).count(),
        'total_municipios': Municipio.objects.count(),
        'total_eventos': Evento.objects.count(),
        'total_participacoes': Participacao.objects.filter(confirmado=True).count(),
    }
    return render(request, 'relatorios/painel.html', ctx)


@login_required
def exportar_excel(request):
    """Exporta relatório completo de engajamento em formato Excel."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    wb = openpyxl.Workbook()

    # Aba 1: Engajamento
    ws = wb.active
    ws.title = 'Engajamento'
    headers = ['Municipio', 'UF', 'Regiao', 'Bienio', 'Pts Brutos', 'Pts Normalizado', 'Participacoes', 'Nivel']
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='1E3A5F', end_color='1E3A5F', fill_type='solid')
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
    for row, eng in enumerate(Engajamento.objects.select_related('municipio').order_by('-pontuacao_bruta'), 2):
        ws.cell(row=row, column=1, value=eng.municipio.nome)
        ws.cell(row=row, column=2, value=eng.municipio.uf)
        ws.cell(row=row, column=3, value=eng.municipio.get_regiao_display())
        ws.cell(row=row, column=4, value=eng.bienio)
        ws.cell(row=row, column=5, value=eng.pontuacao_bruta)
        ws.cell(row=row, column=6, value=eng.pontuacao_normalizada)
        ws.cell(row=row, column=7, value=eng.total_participacoes)
        ws.cell(row=row, column=8, value=eng.get_nivel_display())
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 18

    # Aba 2: Adimplência
    ws2 = wb.create_sheet('Adimplencia')
    headers2 = ['Municipio', 'UF', 'Ano', 'Status', 'Valor Devido', 'Valor Pago']
    for col, h in enumerate(headers2, 1):
        cell = ws2.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
    for row, a in enumerate(Adimplencia.objects.select_related('municipio').order_by('-ano_referencia', 'municipio__nome'), 2):
        ws2.cell(row=row, column=1, value=a.municipio.nome)
        ws2.cell(row=row, column=2, value=a.municipio.uf)
        ws2.cell(row=row, column=3, value=a.ano_referencia)
        ws2.cell(row=row, column=4, value=a.get_status_display())
        ws2.cell(row=row, column=5, value=float(a.valor_devido))
        ws2.cell(row=row, column=6, value=float(a.valor_pago))
    for col in range(1, len(headers2) + 1):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 18

    # Aba 3: Pessoas
    ws3 = wb.create_sheet('Pessoas')
    headers3 = ['Nome', 'Tipo', 'Cargo', 'Partido', 'Status']
    for col, h in enumerate(headers3, 1):
        cell = ws3.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
    for row, p in enumerate(Pessoa.objects.filter(ativo=True).order_by('nome'), 2):
        ws3.cell(row=row, column=1, value=p.nome)
        ws3.cell(row=row, column=2, value=p.get_tipo_display())
        ws3.cell(row=row, column=3, value=p.cargo)
        ws3.cell(row=row, column=4, value=p.partido)
        ws3.cell(row=row, column=5, value='Ativo' if p.ativo else 'Inativo')
    for col in range(1, len(headers3) + 1):
        ws3.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 22

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="relatorio-fnp.xlsx"'
    return response


@login_required
def exportar_pdf(request):
    """Exporta relatório resumido em formato PDF via WeasyPrint."""
    dados = _dados_dashboard()
    engajamentos = Engajamento.objects.select_related('municipio').order_by('-pontuacao_bruta')[:20]
    ctx = {
        'dados': dados,
        'engajamentos': engajamentos,
        'total_pessoas': Pessoa.objects.filter(ativo=True).count(),
        'total_municipios': Municipio.objects.count(),
        'total_eventos': Evento.objects.count(),
    }
    html = render(request, 'relatorios/pdf_relatorio.html', ctx).content.decode('utf-8')

    from xhtml2pdf import pisa
    pdf_buffer = BytesIO()
    pisa.CreatePDF(html, dest=pdf_buffer)
    pdf_buffer.seek(0)

    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relatorio-fnp.pdf"'
    return response
