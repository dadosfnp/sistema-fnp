"""Testes do app relatorios: dashboard, exportacao Excel e PDF."""

import pytest
from django.test import Client

from tests.factories import (
    AdimplenciaFactory, EngajamentoFactory, EventoFactory,
    MunicipioFactory, PessoaFactory, UserFactory,
)


@pytest.mark.django_db
class TestPainelRelatorios:
    def setup_method(self):
        self.user = UserFactory()
        self.client = Client()
        self.client.force_login(self.user)

    def test_painel_carrega(self):
        resp = self.client.get('/relatorios/')
        assert resp.status_code == 200
        assert 'total_pessoas' in resp.context
        assert 'adimplencia_json' in resp.context

    def test_painel_com_dados(self):
        PessoaFactory.create_batch(5)
        MunicipioFactory.create_batch(3)
        EventoFactory.create_batch(2)
        resp = self.client.get('/relatorios/')
        assert resp.context['total_pessoas'] == 5
        assert resp.context['total_municipios'] == 3
        assert resp.context['total_eventos'] == 2


@pytest.mark.django_db
class TestExportacaoExcel:
    def test_exportar_excel(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        PessoaFactory.create_batch(3)
        MunicipioFactory.create_batch(2)
        resp = client.get('/relatorios/exportar/excel/')
        assert resp.status_code == 200
        assert resp['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert 'relatorio-fnp.xlsx' in resp['Content-Disposition']
        assert len(resp.content) > 0


@pytest.mark.django_db
class TestExportacaoPdf:
    def test_exportar_pdf(self):
        user = UserFactory()
        client = Client()
        client.force_login(user)
        EngajamentoFactory.create_batch(2)
        resp = client.get('/relatorios/exportar/pdf/')
        assert resp.status_code == 200
        assert resp['Content-Type'] == 'application/pdf'
        assert 'relatorio-fnp.pdf' in resp['Content-Disposition']
        assert len(resp.content) > 0
