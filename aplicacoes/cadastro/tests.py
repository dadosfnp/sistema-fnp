"""Testes de view do app cadastro — permissões, filtros, paginação, exportação."""

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.nucleo.models import Perfil


class BaseViewTest(TestCase):
    """Setup compartilhado: usuários visualizador, editor e admin."""

    def setUp(self):
        self.cliente_anon = Client()

        self.user_visu = User.objects.create_user('visu', password='senha123')
        Perfil.objects.create(usuario=self.user_visu, tipo=Perfil.TipoPerfil.VISUALIZADOR)

        self.user_editor = User.objects.create_user('editor', password='senha123')
        Perfil.objects.create(usuario=self.user_editor, tipo=Perfil.TipoPerfil.EDITOR)

        self.user_admin = User.objects.create_superuser('admin', 'a@a.com', 'senha123')

        # Dados de mockup
        self.muni_sp = Municipio.objects.create(
            nome='São Paulo', uf='SP', codigo_ibge=3550308,
            regiao='sudeste', eh_capital=True, associado_fnp=True, populacao=12000000,
        )
        self.muni_rj = Municipio.objects.create(
            nome='Rio de Janeiro', uf='RJ', codigo_ibge=3304557,
            regiao='sudeste', eh_capital=True, populacao=6000000,
        )
        self.muni_bsb = Municipio.objects.create(
            nome='Brasília', uf='DF', codigo_ibge=5300108,
            regiao='centro_oeste', eh_capital=True, populacao=3000000,
        )

        self.pessoa_p = Pessoa.objects.create(
            nome='Maria Silva', tipo='prefeito', partido='X', cargo='Prefeita',
        )
        self.pessoa_s = Pessoa.objects.create(
            nome='João Santos', tipo='secretario', partido='Y', cargo='Secretário',
        )


class ListaMunicipiosTest(BaseViewTest):
    """Testes da view lista_municipios — filtros, paginação, exportação."""

    def test_anonimo_redireciona_para_login(self):
        r = self.cliente_anon.get(reverse('cadastro:lista_municipios'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/entrar/', r.url)

    def test_visualizador_acessa_mas_nao_ve_botao_criar(self):
        self.client.login(username='visu', password='senha123')
        r = self.client.get(reverse('cadastro:lista_municipios'))
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, 'Novo Municipio')

    def test_editor_ve_botao_criar(self):
        self.client.login(username='editor', password='senha123')
        r = self.client.get(reverse('cadastro:lista_municipios'))
        self.assertContains(r, 'Novo Municipio')

    def test_filtro_por_uf(self):
        self.client.login(username='editor', password='senha123')
        r = self.client.get(reverse('cadastro:lista_municipios') + '?uf=SP')
        self.assertContains(r, 'São Paulo')
        self.assertNotContains(r, 'Rio de Janeiro')

    def test_filtro_por_regiao(self):
        self.client.login(username='editor', password='senha123')
        r = self.client.get(reverse('cadastro:lista_municipios') + '?regiao=centro_oeste')
        self.assertContains(r, 'Brasília')
        self.assertNotContains(r, 'São Paulo')

    def test_busca_textual(self):
        self.client.login(username='editor', password='senha123')
        r = self.client.get(reverse('cadastro:lista_municipios') + '?busca=São')
        self.assertContains(r, 'São Paulo')
        self.assertNotContains(r, 'Brasília')

    def test_export_csv_respeita_filtros(self):
        self.client.login(username='editor', password='senha123')
        r = self.client.get(reverse('cadastro:lista_municipios') + '?regiao=sudeste&exportar=csv')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('attachment', r['Content-Disposition'])
        conteudo = r.content.decode('utf-8')
        self.assertIn('São Paulo', conteudo)
        self.assertIn('Rio de Janeiro', conteudo)
        self.assertNotIn('Brasília', conteudo)  # filtro de região aplicado

    def test_paginacao(self):
        # Criar 60 municípios para forçar paginação (50 por página)
        for i in range(60):
            Municipio.objects.create(
                nome=f'Cidade {i:02d}', uf='MG', codigo_ibge=1000000 + i,
                regiao='sudeste', populacao=10000,
            )
        self.client.login(username='editor', password='senha123')
        r = self.client.get(reverse('cadastro:lista_municipios'))
        self.assertContains(r, 'Cidade 00')
        r2 = self.client.get(reverse('cadastro:lista_municipios') + '?pagina=2')
        self.assertEqual(r2.status_code, 200)


class ListaPessoasTest(BaseViewTest):
    """Testes da view lista_pessoas — filtros, exportação."""

    def test_filtro_por_tipo(self):
        self.client.login(username='editor', password='senha123')
        r = self.client.get(reverse('cadastro:lista_pessoas') + '?tipo=prefeito')
        self.assertContains(r, 'Maria Silva')
        self.assertNotContains(r, 'João Santos')

    def test_busca_por_cargo(self):
        self.client.login(username='editor', password='senha123')
        r = self.client.get(reverse('cadastro:lista_pessoas') + '?busca=Secretário')
        self.assertContains(r, 'João Santos')
        self.assertNotContains(r, 'Maria Silva')

    def test_export_csv(self):
        self.client.login(username='editor', password='senha123')
        r = self.client.get(reverse('cadastro:lista_pessoas') + '?exportar=csv')
        self.assertEqual(r.status_code, 200)
        conteudo = r.content.decode('utf-8')
        self.assertIn('Maria Silva', conteudo)
        self.assertIn('João Santos', conteudo)

    def test_pessoa_inativa_nao_aparece(self):
        Pessoa.objects.create(nome='Inativo Teste', tipo='prefeito', ativo=False)
        self.client.login(username='editor', password='senha123')
        r = self.client.get(reverse('cadastro:lista_pessoas'))
        self.assertNotContains(r, 'Inativo Teste')


class DetalheMunicipioTest(BaseViewTest):
    """Garante que detalhe carrega via serviço e respeita 404."""

    def test_404_em_uuid_inexistente(self):
        self.client.login(username='visu', password='senha123')
        r = self.client.get('/municipios/00000000-0000-0000-0000-000000000000/')
        self.assertEqual(r.status_code, 404)

    def test_detalhe_carrega_municipio_existente(self):
        self.client.login(username='visu', password='senha123')
        r = self.client.get(reverse('cadastro:detalhe_municipio', args=[self.muni_sp.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'São Paulo')


class PermissoesGranularesTest(BaseViewTest):
    """Verifica que ``Perfil.pode()`` reflete corretamente as permissões."""

    def test_editor_pode_editar_e_exportar(self):
        perfil = self.user_editor.perfil
        self.assertTrue(perfil.pode('pode_editar'))
        self.assertTrue(perfil.pode('pode_exportar'))

    def test_visualizador_nao_pode_editar(self):
        perfil = self.user_visu.perfil
        self.assertFalse(perfil.pode('pode_editar'))
        self.assertFalse(perfil.pode('pode_importar_ibge'))

    def test_permissoes_extras_aditivas(self):
        perfil = self.user_visu.perfil
        perfil.permissoes_extras = ['pode_importar_ibge']
        perfil.save()
        self.assertTrue(perfil.pode('pode_importar_ibge'))
        self.assertFalse(perfil.pode('pode_editar'))

    def test_admin_pode_tudo(self):
        # superuser sem perfil — testar via Perfil.tipo=admin
        u = User.objects.create_user('a2', password='senha')
        p = Perfil.objects.create(usuario=u, tipo=Perfil.TipoPerfil.ADMIN)
        self.assertTrue(p.pode('pode_importar_ibge'))
        self.assertTrue(p.pode('qualquer_coisa_inventada'))


class SoftDeleteTest(BaseViewTest):
    """Testa arquivar/desarquivar de ModeloBase."""

    def test_arquivar_marca_campo(self):
        self.muni_sp.arquivar()
        self.muni_sp.refresh_from_db()
        self.assertIsNotNone(self.muni_sp.arquivado_em)
        self.assertTrue(self.muni_sp.arquivado)

    def test_manager_ativos_filtra_arquivados(self):
        self.muni_sp.arquivar()
        self.assertEqual(Municipio.ativos.count(), 2)  # rj e bsb
        self.assertEqual(Municipio.objects.count(), 3)  # ainda no banco

    def test_desarquivar_reverte(self):
        self.muni_sp.arquivar()
        self.muni_sp.desarquivar()
        self.assertIsNone(self.muni_sp.arquivado_em)


class BuscaGlobalTest(BaseViewTest):
    """Endpoint /api/busca/ usado pelo command palette."""

    def test_requer_login(self):
        r = self.cliente_anon.get(reverse('nucleo:busca_global') + '?q=Maria')
        self.assertEqual(r.status_code, 302)

    def test_termo_curto_retorna_vazio(self):
        self.client.login(username='visu', password='senha123')
        r = self.client.get(reverse('nucleo:busca_global') + '?q=a')
        self.assertEqual(r.json()['resultados'], [])

    def test_busca_encontra_pessoa(self):
        self.client.login(username='visu', password='senha123')
        r = self.client.get(reverse('nucleo:busca_global') + '?q=Maria')
        resultados = r.json()['resultados']
        self.assertTrue(any('Maria Silva' in x['titulo'] for x in resultados))

    def test_busca_encontra_municipio_por_uf(self):
        self.client.login(username='visu', password='senha123')
        r = self.client.get(reverse('nucleo:busca_global') + '?q=SP')
        resultados = r.json()['resultados']
        self.assertTrue(any('São Paulo' in x['titulo'] for x in resultados))
