"""Testes do motor de engajamento: calculo, signals e normalizacao."""

import pytest
from datetime import date
from django.test import Client

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.engajamento.models import ConfiguracaoEngajamento, Engajamento
from aplicacoes.eventos.models import Evento, Participacao
from tests.factories import (
    AdimplenciaFactory, EngajamentoFactory, EventoFactory,
    MunicipioFactory, ParticipacaoFactory, PessoaFactory,
    UserFactory, VinculoMunicipioFactory,
)


@pytest.mark.django_db
class TestMotorEngajamento:
    """Testa o algoritmo de recalculo de engajamento."""

    def _setup_cenario(self, n_eventos=1, participou=True, status_adimplencia='adimplente'):
        """Cria cenario padrao: 1 municipio, 1 pessoa, N eventos."""
        config = ConfiguracaoEngajamento.atual()
        mun = MunicipioFactory()
        pessoa = PessoaFactory()
        VinculoMunicipioFactory(pessoa=pessoa, municipio=mun)

        eventos = []
        for i in range(n_eventos):
            ev = EventoFactory(
                data_inicio=date(2026, 3 + i, 15),
                pontos_presencial=10,
                pontos_online=5,
            )
            eventos.append(ev)
            if participou:
                ParticipacaoFactory(
                    pessoa=pessoa, evento=ev, municipio=mun,
                    forma_participacao='presencial', confirmado=True,
                )

        AdimplenciaFactory(
            municipio=mun, ano_referencia=2026, status=status_adimplencia,
        )

        eng = Engajamento.objects.get(municipio=mun, bienio=config.bienio_atual)
        return eng, mun, pessoa, eventos

    def test_participou_de_todos_os_eventos_score_100(self):
        eng, *_ = self._setup_cenario(n_eventos=3, participou=True, status_adimplencia='adimplente')
        # 3 eventos x 10 pts = 30 meta, 30 pts obtidos = 100%
        assert eng.pontuacao_normalizada == 100
        assert eng.nivel == Engajamento.Nivel.ALTO

    def test_nao_participou_score_zero(self):
        config = ConfiguracaoEngajamento.atual()
        mun = MunicipioFactory()
        EventoFactory(data_inicio=date(2026, 3, 15), pontos_presencial=10)
        AdimplenciaFactory(municipio=mun, ano_referencia=2026, status='adimplente')
        eng, _ = Engajamento.objects.get_or_create(municipio=mun, bienio=config.bienio_atual)
        eng.recalcular()
        assert eng.pontuacao_normalizada == 0
        assert eng.nivel == Engajamento.Nivel.INATIVO

    def test_penalidade_inadimplente_30_porcento(self):
        eng, *_ = self._setup_cenario(n_eventos=1, participou=True, status_adimplencia='inadimplente')
        # 10 pts obtidos, meta 10, penalidade 30% = 3 pts perdidos
        # Liquido: 7, normalizado: 70%
        assert eng.pontuacao_normalizada == 70

    def test_penalidade_parcial_15_porcento(self):
        eng, *_ = self._setup_cenario(n_eventos=1, participou=True, status_adimplencia='parcial')
        # 10 pts, penalidade 15% = 1.5 → 1 pt perdido (int)
        # Liquido: 9, normalizado: 90%
        assert eng.pontuacao_normalizada == 90

    def test_meta_dinamica(self):
        """Meta = soma de pontos_presencial de todos os eventos do bienio."""
        config = ConfiguracaoEngajamento.atual()
        mun = MunicipioFactory()
        pessoa = PessoaFactory()
        VinculoMunicipioFactory(pessoa=pessoa, municipio=mun)

        ev1 = EventoFactory(data_inicio=date(2026, 1, 10), pontos_presencial=10)
        ev2 = EventoFactory(data_inicio=date(2026, 2, 10), pontos_presencial=20)
        # Meta = 10 + 20 = 30

        ParticipacaoFactory(pessoa=pessoa, evento=ev1, municipio=mun, confirmado=True)
        # Participou so do ev1 (10 pts de 30 = 33%)

        AdimplenciaFactory(municipio=mun, ano_referencia=2026, status='adimplente')
        eng = Engajamento.objects.get(municipio=mun, bienio=config.bienio_atual)
        assert eng.pontuacao_normalizada == 33

    def test_nivel_alto_muitas_participacoes(self):
        """Municipio que participa de todos os eventos tem nivel alto."""
        eng, *_ = self._setup_cenario(n_eventos=5, participou=True, status_adimplencia='adimplente')
        assert eng.nivel == Engajamento.Nivel.ALTO

    def test_nivel_inativo_sem_participacao(self):
        """Municipio sem participacao tem nivel inativo."""
        config = ConfiguracaoEngajamento.atual()
        mun = MunicipioFactory()
        EventoFactory(data_inicio=date(2026, 3, 15))
        AdimplenciaFactory(municipio=mun, ano_referencia=2026)
        eng, _ = Engajamento.objects.get_or_create(municipio=mun, bienio=config.bienio_atual)
        eng.recalcular()
        assert eng.nivel == Engajamento.Nivel.INATIVO


@pytest.mark.django_db
class TestSignals:
    """Testa que signals recalculam engajamento automaticamente."""

    def test_signal_ao_salvar_participacao(self):
        config = ConfiguracaoEngajamento.atual()
        mun = MunicipioFactory()
        pessoa = PessoaFactory()
        VinculoMunicipioFactory(pessoa=pessoa, municipio=mun)
        ev = EventoFactory(data_inicio=date(2026, 1, 15), pontos_presencial=10)

        # Antes: sem participacao
        eng, _ = Engajamento.objects.get_or_create(municipio=mun, bienio=config.bienio_atual)
        eng.recalcular()
        assert eng.total_participacoes == 0

        # Criar participacao — signal deve recalcular
        ParticipacaoFactory(pessoa=pessoa, evento=ev, municipio=mun, confirmado=True)
        eng.refresh_from_db()
        assert eng.total_participacoes == 1
        assert eng.pontuacao_bruta > 0

    def test_signal_ao_deletar_participacao(self):
        config = ConfiguracaoEngajamento.atual()
        mun = MunicipioFactory()
        pessoa = PessoaFactory()
        VinculoMunicipioFactory(pessoa=pessoa, municipio=mun)
        ev = EventoFactory(data_inicio=date(2026, 1, 15))
        part = ParticipacaoFactory(pessoa=pessoa, evento=ev, municipio=mun, confirmado=True)

        eng = Engajamento.objects.get(municipio=mun, bienio=config.bienio_atual)
        assert eng.total_participacoes == 1

        part.delete()
        eng.refresh_from_db()
        assert eng.total_participacoes == 0

    def test_signal_ao_mudar_adimplencia(self):
        config = ConfiguracaoEngajamento.atual()
        mun = MunicipioFactory()
        pessoa = PessoaFactory()
        VinculoMunicipioFactory(pessoa=pessoa, municipio=mun)
        ev = EventoFactory(data_inicio=date(2026, 1, 15), pontos_presencial=10)
        ParticipacaoFactory(pessoa=pessoa, evento=ev, municipio=mun, confirmado=True)

        # Adimplente — sem penalidade
        adim = AdimplenciaFactory(municipio=mun, ano_referencia=2026, status='adimplente')
        eng = Engajamento.objects.get(municipio=mun, bienio=config.bienio_atual)
        score_antes = eng.pontuacao_normalizada

        # Mudar para inadimplente — signal recalcula com penalidade
        adim.status = 'inadimplente'
        adim.save()
        eng.refresh_from_db()
        assert eng.pontuacao_normalizada < score_antes


@pytest.mark.django_db
class TestEngajamentoViews:
    def test_lista_engajamento(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        resp = client.get('/engajamento/')
        assert resp.status_code == 200

    def test_filtro_nivel(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        EngajamentoFactory(nivel='alto', pontuacao_normalizada=80)
        EngajamentoFactory(nivel='baixo', pontuacao_normalizada=20)
        resp = client.get('/engajamento/', {'nivel': 'alto'})
        assert len(resp.context['engajamentos']) == 1
