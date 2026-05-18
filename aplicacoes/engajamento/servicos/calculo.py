"""Serviço de cálculo de engajamento — registry pluggável de fontes de pontos.

Cada categoria do sistema (eventos, instâncias, missões, atividades) registra
uma função que sabe calcular quantos pontos um município ganha em determinado
biênio. Adicionar uma nova fonte vira usar ``@registrar_fonte('chave')`` em
qualquer lugar do código, sem mexer no calculo central.

Exemplo de uso:

    from aplicacoes.engajamento.servicos.calculo import registrar_fonte

    @registrar_fonte('formacao')
    def pontos_formacao(municipio, ano1, ano2):
        return PontosDeFonte(ano_atual=10, ano_anterior=5, total_itens=2)

A função recebe o município e os dois anos do biênio, e devolve um
``PontosDeFonte`` com a distribuição temporal e a contagem de itens.
"""

from dataclasses import dataclass
from typing import Callable, Dict


@dataclass
class PontosDeFonte:
    """Pontos calculados por uma única fonte (evento, missão, atividade, etc.).

    Atributos:
        ano_atual: pontos atribuídos ao ano corrente (não decai).
        ano_anterior: pontos do ano anterior (sofre decaimento).
        total_itens: contagem de itens contabilizados (para totalização).
    """
    ano_atual: int = 0
    ano_anterior: int = 0
    total_itens: int = 0


FonteFn = Callable[[object, int, int], PontosDeFonte]

# Registry global: chave -> função. Populado pelos módulos das categorias
# importados via apps.ready() (ver EngajamentoConfig.ready).
_FONTES: Dict[str, FonteFn] = {}


def registrar_fonte(chave):
    """Decorator que adiciona uma função ao registry de fontes."""
    def _wrapper(fn):
        _FONTES[chave] = fn
        return fn
    return _wrapper


def fontes_registradas():
    """Retorna o dict imutável de fontes — útil para debugging e testes."""
    return dict(_FONTES)


def calcular_pontos(municipio, ano1, ano2):
    """Agrega contribuições de todas as fontes registradas.

    Returns:
        Tupla ``(ano_atual_total, ano_anterior_total, total_itens, detalhes)``.
        ``detalhes`` é dict chave -> PontosDeFonte para auditoria.
    """
    detalhes = {}
    for chave, fn in _FONTES.items():
        try:
            detalhes[chave] = fn(municipio, ano1, ano2)
        except Exception:
            # Uma fonte com bug não pode quebrar o cálculo inteiro.
            detalhes[chave] = PontosDeFonte()

    ano_atual = sum(p.ano_atual for p in detalhes.values())
    ano_anterior = sum(p.ano_anterior for p in detalhes.values())
    total = sum(p.total_itens for p in detalhes.values())
    return ano_atual, ano_anterior, total, detalhes


def registrar_fontes_default():
    """Registra as fontes built-in do sistema.

    Chamado em ``EngajamentoConfig.ready()``. Evita import circular ao importar
    aqui (dentro da função) em vez de no topo do módulo.
    """
    from django.utils import timezone

    from aplicacoes.engajamento.models import PesoEngajamento

    @registrar_fonte('eventos')
    def _eventos(municipio, ano1, ano2):
        from aplicacoes.eventos.models import Participacao
        participacoes = Participacao.objects.filter(
            municipio=municipio, confirmado=True,
            evento__data_inicio__year__in=[ano1, ano2],
        )
        ano2_pts = sum(p.pontos_calculados for p in participacoes.filter(evento__data_inicio__year=ano2))
        ano1_pts = sum(p.pontos_calculados for p in participacoes.filter(evento__data_inicio__year=ano1))
        ano_corrente = timezone.now().year
        if ano_corrente >= ano2:
            return PontosDeFonte(ano_atual=ano2_pts, ano_anterior=ano1_pts, total_itens=participacoes.count())
        return PontosDeFonte(ano_atual=ano1_pts, ano_anterior=0, total_itens=participacoes.count())

    @registrar_fonte('representacoes')
    def _representacoes(municipio, ano1, ano2):
        from aplicacoes.instancias.models import Representacao
        pessoas = municipio.vinculos.filter(vigente=True).values_list('pessoa_id', flat=True)
        reps = Representacao.objects.filter(pessoa_id__in=pessoas, vigente=True)
        peso_titular = PesoEngajamento.valor(PesoEngajamento.Chave.REPRESENTACAO_TITULAR, 20)
        peso_suplente = PesoEngajamento.valor(PesoEngajamento.Chave.REPRESENTACAO_SUPLENTE, 10)
        peso_diretiva = PesoEngajamento.valor(PesoEngajamento.Chave.REPRESENTACAO_DIRETIVA, 30)
        diretivas = {
            Representacao.Funcao.PRESIDENTE, Representacao.Funcao.VICE_PRESIDENTE,
            Representacao.Funcao.SECRETARIO_GERAL, Representacao.Funcao.SECRETARIO_EXECUTIVO,
            Representacao.Funcao.DIRETOR_TEMATICO, Representacao.Funcao.DIRETOR_REGIONAL,
        }
        total = 0
        for r in reps:
            if r.funcao in diretivas:
                total += peso_diretiva
            elif r.funcao == Representacao.Funcao.SUPLENTE:
                total += peso_suplente
            else:
                total += peso_titular
        return PontosDeFonte(ano_atual=total, ano_anterior=0, total_itens=reps.count())

    @registrar_fonte('presencas_atividade')
    def _presencas(municipio, ano1, ano2):
        from aplicacoes.presenca.models import Presenca
        presencas = Presenca.objects.filter(
            municipio=municipio, status=Presenca.Status.PRESENTE,
            atividade__data_reuniao__year__in=[ano1, ano2],
        )
        peso = PesoEngajamento.valor(PesoEngajamento.Chave.PRESENCA_ATIVIDADE, 5)
        return PontosDeFonte(ano_atual=presencas.count() * peso, total_itens=presencas.count())

    @registrar_fonte('missoes')
    def _missoes(municipio, ano1, ano2):
        from aplicacoes.missoes.models import MembroDelegacao, Missao
        pessoas = municipio.vinculos.filter(vigente=True).values_list('pessoa_id', flat=True)
        membros = MembroDelegacao.objects.filter(
            pessoa_id__in=pessoas, missao__data_inicio__year__in=[ano1, ano2],
        ).select_related('missao')
        peso_intl = PesoEngajamento.valor(PesoEngajamento.Chave.MISSAO_INTERNACIONAL, 30)
        peso_nac = PesoEngajamento.valor(PesoEngajamento.Chave.MISSAO_NACIONAL, 15)
        total = sum(peso_intl if m.missao.tipo == Missao.Tipo.INTERNACIONAL else peso_nac for m in membros)
        return PontosDeFonte(ano_atual=total, total_itens=membros.count())
