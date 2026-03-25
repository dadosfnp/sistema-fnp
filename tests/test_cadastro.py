"""Testes do app cadastro: models, views de listagem/detalhe e CRUD."""

import pytest
from django.test import Client

from aplicacoes.cadastro.models import Pessoa, Municipio
from aplicacoes.nucleo.models import LogAlteracao, Perfil
from tests.factories import (
    MunicipioFactory, PessoaFactory, PerfilFactory, UserFactory,
    VinculoMunicipioFactory, AdimplenciaFactory,
)


# --- Models ---

@pytest.mark.django_db
class TestPessoaModel:
    def test_str(self):
        p = PessoaFactory(nome='Joao Silva')
        assert str(p) == 'Joao Silva'

    def test_mandato_vigente_true(self):
        from datetime import date
        p = PessoaFactory(mandato_inicio=date(2020, 1, 1), mandato_fim=date(2030, 12, 31))
        assert p.mandato_vigente is True

    def test_mandato_vigente_false(self):
        from datetime import date
        p = PessoaFactory(mandato_inicio=date(2010, 1, 1), mandato_fim=date(2014, 12, 31))
        assert p.mandato_vigente is False

    def test_mandato_vigente_sem_datas(self):
        p = PessoaFactory(mandato_inicio=None, mandato_fim=None)
        assert p.mandato_vigente is False


@pytest.mark.django_db
class TestMunicipioModel:
    def test_str(self):
        m = MunicipioFactory(nome='Campinas', uf='SP')
        assert str(m) == 'Campinas/SP'

    def test_adimplencia_atual_com_registro(self):
        m = MunicipioFactory()
        AdimplenciaFactory(municipio=m, ano_referencia=2025, status='inadimplente')
        AdimplenciaFactory(municipio=m, ano_referencia=2026, status='adimplente')
        assert m.adimplencia_atual == 'adimplente'

    def test_adimplencia_atual_sem_registro(self):
        m = MunicipioFactory()
        assert m.adimplencia_atual is None


# --- Views de listagem ---

@pytest.mark.django_db
class TestListaViews:
    def setup_method(self):
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_lista_pessoas(self):
        PessoaFactory.create_batch(3)
        resp = self.client.get('/cadastro/pessoas/')
        assert resp.status_code == 200
        assert len(resp.context['pessoas']) == 3

    def test_busca_pessoas(self):
        PessoaFactory(nome='Maria Teste')
        PessoaFactory(nome='Joao Outro')
        resp = self.client.get('/cadastro/pessoas/', {'busca': 'Maria'})
        assert len(resp.context['pessoas']) == 1

    def test_filtro_tipo_pessoas(self):
        PessoaFactory(tipo='prefeito')
        PessoaFactory(tipo='secretario')
        resp = self.client.get('/cadastro/pessoas/', {'tipo': 'prefeito'})
        assert len(resp.context['pessoas']) == 1

    def test_htmx_retorna_parcial(self):
        PessoaFactory()
        resp = self.client.get('/cadastro/pessoas/', HTTP_HX_REQUEST='true')
        assert resp.status_code == 200
        assert 'lista_pessoas.html' not in [t.name for t in resp.templates]

    def test_lista_municipios(self):
        MunicipioFactory.create_batch(2)
        resp = self.client.get('/cadastro/municipios/')
        assert resp.status_code == 200
        assert len(resp.context['municipios']) == 2

    def test_filtro_uf_municipios(self):
        MunicipioFactory(uf='SP')
        MunicipioFactory(uf='RJ')
        resp = self.client.get('/cadastro/municipios/', {'uf': 'RJ'})
        assert len(resp.context['municipios']) == 1

    def test_filtro_regiao_municipios(self):
        MunicipioFactory(regiao='sul')
        MunicipioFactory(regiao='sudeste')
        resp = self.client.get('/cadastro/municipios/', {'regiao': 'sul'})
        assert len(resp.context['municipios']) == 1


# --- Views de detalhe ---

@pytest.mark.django_db
class TestDetalheViews:
    def setup_method(self):
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_detalhe_pessoa(self):
        p = PessoaFactory()
        resp = self.client.get(f'/cadastro/pessoas/{p.pk}/')
        assert resp.status_code == 200
        assert resp.context['pessoa'] == p

    def test_detalhe_municipio(self):
        m = MunicipioFactory()
        resp = self.client.get(f'/cadastro/municipios/{m.pk}/')
        assert resp.status_code == 200
        assert resp.context['municipio'] == m

    def test_detalhe_pessoa_404(self):
        import uuid
        resp = self.client.get(f'/cadastro/pessoas/{uuid.uuid4()}/')
        assert resp.status_code == 404


# --- CRUD (editor) ---

@pytest.mark.django_db
class TestCrudPessoa:
    def setup_method(self):
        self.perfil = PerfilFactory(tipo=Perfil.TipoPerfil.EDITOR)
        self.client = Client()
        self.client.force_login(self.perfil.usuario)

    def test_criar_pessoa(self):
        resp = self.client.post('/cadastro/pessoas/novo/', {
            'nome': 'Nova Pessoa',
            'tipo': 'prefeito',
            'genero': 'nao_informado',
            'ativo': True,
        })
        assert resp.status_code == 302
        assert Pessoa.objects.filter(nome='Nova Pessoa').exists()
        assert LogAlteracao.objects.filter(acao='criacao', modelo='Pessoa').exists()

    def test_editar_pessoa(self):
        p = PessoaFactory(nome='Antigo Nome')
        resp = self.client.post(f'/cadastro/pessoas/{p.pk}/editar/', {
            'nome': 'Novo Nome',
            'tipo': p.tipo,
            'genero': p.genero,
            'ativo': True,
        })
        assert resp.status_code == 302
        p.refresh_from_db()
        assert p.nome == 'Novo Nome'
        assert LogAlteracao.objects.filter(acao='edicao').exists()

    def test_visualizador_nao_pode_criar(self):
        perfil_v = PerfilFactory(tipo=Perfil.TipoPerfil.VISUALIZADOR)
        client = Client()
        client.force_login(perfil_v.usuario)
        resp = client.post('/cadastro/pessoas/novo/', {'nome': 'X', 'tipo': 'prefeito', 'genero': 'nao_informado', 'ativo': True})
        assert resp.status_code == 302  # redirect com erro
        assert not Pessoa.objects.filter(nome='X').exists()


@pytest.mark.django_db
class TestCrudMunicipio:
    def setup_method(self):
        self.perfil = PerfilFactory(tipo=Perfil.TipoPerfil.EDITOR)
        self.client = Client()
        self.client.force_login(self.perfil.usuario)

    def test_criar_municipio(self):
        resp = self.client.post('/cadastro/municipios/novo/', {
            'nome': 'Cidade Teste',
            'uf': 'SP',
            'codigo_ibge': 9999999,
            'populacao': 100000,
            'regiao': 'sudeste',
        })
        assert resp.status_code == 302
        assert Municipio.objects.filter(nome='Cidade Teste').exists()

    def test_editar_municipio(self):
        m = MunicipioFactory(populacao=100)
        resp = self.client.post(f'/cadastro/municipios/{m.pk}/editar/', {
            'nome': m.nome, 'uf': m.uf, 'codigo_ibge': m.codigo_ibge,
            'populacao': 999999, 'regiao': m.regiao,
        })
        assert resp.status_code == 302
        m.refresh_from_db()
        assert m.populacao == 999999
