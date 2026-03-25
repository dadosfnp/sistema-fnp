"""Testes do app adimplencia: model, views e CRUD."""

import pytest
from django.test import Client

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.nucleo.models import Perfil
from tests.factories import AdimplenciaFactory, MunicipioFactory, PerfilFactory, UserFactory


@pytest.mark.django_db
class TestAdimplenciaModel:
    def test_str(self):
        a = AdimplenciaFactory(ano_referencia=2026, status='adimplente')
        assert '2026' in str(a)
        assert 'Adimplente' in str(a)

    def test_unique_municipio_ano(self):
        m = MunicipioFactory()
        AdimplenciaFactory(municipio=m, ano_referencia=2026)
        with pytest.raises(Exception):
            AdimplenciaFactory(municipio=m, ano_referencia=2026)


@pytest.mark.django_db
class TestAdimplenciaViews:
    def setup_method(self):
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_lista(self):
        AdimplenciaFactory.create_batch(3)
        resp = self.client.get('/adimplencia/')
        assert resp.status_code == 200
        assert len(resp.context['registros']) == 3

    def test_filtro_status(self):
        AdimplenciaFactory(status='adimplente')
        AdimplenciaFactory(status='inadimplente')
        resp = self.client.get('/adimplencia/', {'status': 'adimplente'})
        assert len(resp.context['registros']) == 1

    def test_filtro_ano(self):
        AdimplenciaFactory(ano_referencia=2025)
        AdimplenciaFactory(ano_referencia=2026)
        resp = self.client.get('/adimplencia/', {'ano': '2025'})
        assert len(resp.context['registros']) == 1


@pytest.mark.django_db
class TestAdimplenciaCrud:
    def test_editor_pode_criar(self):
        perfil = PerfilFactory(tipo=Perfil.TipoPerfil.EDITOR)
        mun = MunicipioFactory()
        client = Client()
        client.force_login(perfil.usuario)
        resp = client.post('/adimplencia/novo/', {
            'municipio': mun.pk,
            'ano_referencia': 2027,
            'status': 'adimplente',
            'valor_devido': '50000.00',
            'valor_pago': '50000.00',
        })
        assert resp.status_code == 302
        assert Adimplencia.objects.filter(ano_referencia=2027).exists()
