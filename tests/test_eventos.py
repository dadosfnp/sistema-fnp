"""Testes do app eventos: calculo de pontos, views e CRUD."""

import pytest
from datetime import date
from django.test import Client

from aplicacoes.eventos.models import Evento, Participacao
from aplicacoes.nucleo.models import Perfil
from tests.factories import (
    EventoFactory, MunicipioFactory, ParticipacaoFactory,
    PerfilFactory, PessoaFactory, UserFactory,
)


@pytest.mark.django_db
class TestCalculoPontos:
    """Testa o calculo automatico de pontos no save() da Participacao."""

    def test_presencial_participante(self):
        ev = EventoFactory(pontos_presencial=10, pontos_online=5)
        p = ParticipacaoFactory(
            evento=ev, forma_participacao='presencial',
            papel_no_evento='participante', confirmado=True,
        )
        assert p.pontos_calculados == 10

    def test_online_participante(self):
        ev = EventoFactory(pontos_presencial=10, pontos_online=5)
        p = ParticipacaoFactory(
            evento=ev, forma_participacao='online',
            papel_no_evento='participante', confirmado=True,
        )
        assert p.pontos_calculados == 5

    def test_presencial_palestrante(self):
        ev = EventoFactory(pontos_presencial=10, pontos_palestrante_bonus=5)
        p = ParticipacaoFactory(
            evento=ev, forma_participacao='presencial',
            papel_no_evento='palestrante', confirmado=True,
        )
        assert p.pontos_calculados == 15  # 10 + 5

    def test_presencial_organizador(self):
        ev = EventoFactory(pontos_presencial=10, pontos_organizador_bonus=5)
        p = ParticipacaoFactory(
            evento=ev, forma_participacao='presencial',
            papel_no_evento='organizador', confirmado=True,
        )
        assert p.pontos_calculados == 15

    def test_online_palestrante(self):
        ev = EventoFactory(pontos_online=5, pontos_palestrante_bonus=5)
        p = ParticipacaoFactory(
            evento=ev, forma_participacao='online',
            papel_no_evento='palestrante', confirmado=True,
        )
        assert p.pontos_calculados == 10  # 5 + 5

    def test_moderador_sem_bonus(self):
        ev = EventoFactory(pontos_presencial=10)
        p = ParticipacaoFactory(
            evento=ev, forma_participacao='presencial',
            papel_no_evento='moderador', confirmado=True,
        )
        assert p.pontos_calculados == 10  # sem bonus extra

    def test_unique_pessoa_evento(self):
        pessoa = PessoaFactory()
        evento = EventoFactory()
        mun = MunicipioFactory()
        ParticipacaoFactory(pessoa=pessoa, evento=evento, municipio=mun)
        with pytest.raises(Exception):
            ParticipacaoFactory(pessoa=pessoa, evento=evento, municipio=mun)


@pytest.mark.django_db
class TestEventoModel:
    def test_str(self):
        ev = EventoFactory(titulo='Forum Nacional')
        assert 'Forum Nacional' in str(ev)

    def test_ordering(self):
        ev1 = EventoFactory(data_inicio=date(2025, 1, 1))
        ev2 = EventoFactory(data_inicio=date(2026, 1, 1))
        eventos = list(Evento.objects.all())
        assert eventos[0] == ev2  # mais recente primeiro


@pytest.mark.django_db
class TestEventoViews:
    def setup_method(self):
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_lista_eventos(self):
        EventoFactory.create_batch(3)
        resp = self.client.get('/eventos/')
        assert resp.status_code == 200
        assert len(resp.context['eventos']) == 3

    def test_filtro_tipo(self):
        EventoFactory(tipo='forum')
        EventoFactory(tipo='webinar')
        resp = self.client.get('/eventos/', {'tipo': 'forum'})
        assert len(resp.context['eventos']) == 1

    def test_filtro_modalidade(self):
        EventoFactory(modalidade='presencial')
        EventoFactory(modalidade='online')
        resp = self.client.get('/eventos/', {'modalidade': 'online'})
        assert len(resp.context['eventos']) == 1

    def test_detalhe_evento(self):
        ev = EventoFactory()
        resp = self.client.get(f'/eventos/{ev.pk}/')
        assert resp.status_code == 200
        assert resp.context['evento'] == ev


@pytest.mark.django_db
class TestEventoCrud:
    def test_editor_pode_criar_evento(self):
        perfil = PerfilFactory(tipo=Perfil.TipoPerfil.EDITOR)
        client = Client()
        client.force_login(perfil.usuario)
        resp = client.post('/eventos/novo/', {
            'titulo': 'Evento Teste',
            'tipo': 'forum',
            'modalidade': 'presencial',
            'data_inicio': '2026-06-15',
            'pontos_presencial': 10,
            'pontos_online': 5,
            'pontos_palestrante_bonus': 5,
            'pontos_organizador_bonus': 5,
        })
        assert resp.status_code == 302
        assert Evento.objects.filter(titulo='Evento Teste').exists()

    def test_editor_pode_registrar_participacao(self):
        perfil = PerfilFactory(tipo=Perfil.TipoPerfil.EDITOR)
        pessoa = PessoaFactory()
        evento = EventoFactory()
        mun = MunicipioFactory()
        client = Client()
        client.force_login(perfil.usuario)
        resp = client.post('/eventos/participacao/novo/', {
            'pessoa': pessoa.pk,
            'evento': evento.pk,
            'municipio': mun.pk,
            'forma_participacao': 'presencial',
            'papel_no_evento': 'participante',
            'confirmado': True,
        })
        assert resp.status_code == 302
        assert Participacao.objects.filter(pessoa=pessoa, evento=evento).exists()
