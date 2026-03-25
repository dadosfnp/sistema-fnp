"""Testes do app nucleo: models, views de auth, auditoria e context processor."""

import pytest
from django.test import Client

from aplicacoes.nucleo.models import LogAlteracao, Perfil
from aplicacoes.nucleo.servicos.auditoria import (
    detectar_alteracoes,
    registrar_criacao,
    registrar_edicao,
    registrar_exclusao,
)
from tests.factories import PessoaFactory, PerfilFactory, UserFactory


# --- Models ---

@pytest.mark.django_db
class TestPerfil:
    def test_criar_perfil_visualizador(self):
        perfil = PerfilFactory(tipo=Perfil.TipoPerfil.VISUALIZADOR)
        assert perfil.eh_editor is False

    def test_criar_perfil_editor(self):
        perfil = PerfilFactory(tipo=Perfil.TipoPerfil.EDITOR)
        assert perfil.eh_editor is True

    def test_str(self):
        perfil = PerfilFactory()
        assert '—' in str(perfil)


# --- Auditoria ---

@pytest.mark.django_db
class TestAuditoria:
    def test_registrar_criacao(self):
        user = UserFactory()
        pessoa = PessoaFactory()
        registrar_criacao(user, pessoa)
        log = LogAlteracao.objects.last()
        assert log.acao == LogAlteracao.TipoAcao.CRIACAO
        assert log.modelo == 'Pessoa'
        assert log.usuario == user

    def test_registrar_edicao_com_alteracoes(self):
        user = UserFactory()
        pessoa = PessoaFactory()
        registrar_edicao(user, pessoa, {'nome': {'antes': 'A', 'depois': 'B'}})
        log = LogAlteracao.objects.last()
        assert log.acao == LogAlteracao.TipoAcao.EDICAO
        assert 'nome' in log.campos_alterados

    def test_registrar_edicao_sem_alteracoes_nao_cria_log(self):
        user = UserFactory()
        pessoa = PessoaFactory()
        registrar_edicao(user, pessoa, {})
        assert LogAlteracao.objects.count() == 0

    def test_registrar_exclusao(self):
        user = UserFactory()
        pessoa = PessoaFactory()
        registrar_exclusao(user, pessoa)
        log = LogAlteracao.objects.last()
        assert log.acao == LogAlteracao.TipoAcao.EXCLUSAO

    def test_detectar_alteracoes(self):
        pessoa = PessoaFactory(nome='Carlos', partido='PSD')
        alteracoes = detectar_alteracoes(pessoa, {'nome': 'Carlos', 'partido': 'MDB'})
        assert 'partido' in alteracoes
        assert 'nome' not in alteracoes
        assert alteracoes['partido']['antes'] == 'PSD'
        assert alteracoes['partido']['depois'] == 'MDB'


# --- Views ---

@pytest.mark.django_db
class TestViewsAuth:
    def test_login_page_acessivel(self):
        client = Client()
        resp = client.get('/entrar/')
        assert resp.status_code == 200

    def test_redirect_para_login_sem_autenticacao(self):
        client = Client()
        resp = client.get('/')
        assert resp.status_code == 302
        assert '/entrar/' in resp.url

    def test_login_com_credenciais_validas(self):
        user = UserFactory(username='teste')
        client = Client()
        resp = client.post('/entrar/', {'usuario': 'teste', 'senha': 'senha123'})
        assert resp.status_code == 302
        assert resp.url == '/'

    def test_login_com_credenciais_invalidas(self):
        client = Client()
        resp = client.post('/entrar/', {'usuario': 'x', 'senha': 'y'})
        assert resp.status_code == 200
        assert 'incorretos' in resp.content.decode()

    def test_logout_redireciona(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        resp = client.get('/sair/')
        assert resp.status_code == 302

    def test_inicio_autenticado(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        resp = client.get('/')
        assert resp.status_code == 200


# --- Context Processor ---

@pytest.mark.django_db
class TestContextProcessor:
    def test_eh_editor_para_superuser(self):
        user = UserFactory(is_superuser=True)
        client = Client()
        client.force_login(user)
        resp = client.get('/')
        assert resp.context['eh_editor'] is True

    def test_eh_editor_para_editor(self):
        perfil = PerfilFactory(tipo=Perfil.TipoPerfil.EDITOR)
        client = Client()
        client.force_login(perfil.usuario)
        resp = client.get('/')
        assert resp.context['eh_editor'] is True

    def test_eh_editor_para_visualizador(self):
        perfil = PerfilFactory(tipo=Perfil.TipoPerfil.VISUALIZADOR)
        client = Client()
        client.force_login(perfil.usuario)
        resp = client.get('/')
        assert resp.context['eh_editor'] is False
