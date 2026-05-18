"""Servico de exportacao universal — converte querysets filtrados em CSV.

CSV escolhido por ser leve, portavel e compativel com qualquer planilha.
O caller passa colunas (header) e funcao que extrai valores de cada objeto.
"""

import csv

from django.http import HttpResponse


def exportar_csv(nome_arquivo, cabecalho, linhas_iter):
    """Gera HttpResponse CSV streaming-friendly.

    Args:
        nome_arquivo: Nome sem extensao do arquivo (sera adicionado .csv).
        cabecalho: Lista de strings com nomes das colunas.
        linhas_iter: Iteravel de listas/tuplas com valores (uma por registro).

    Returns:
        HttpResponse com Content-Type CSV e Content-Disposition de download.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}.csv"'
    # BOM para Excel reconhecer UTF-8 corretamente com acentos
    response.write('﻿')

    writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(cabecalho)
    for linha in linhas_iter:
        writer.writerow(linha)
    return response
