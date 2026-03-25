"""Factories para todos os models do sistema — usadas nos testes com pytest."""

import factory
from django.contrib.auth.models import User
from factory.django import DjangoModelFactory

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.cadastro.models import Municipio, Pauta, Pessoa, VinculoMunicipio
from aplicacoes.engajamento.models import ConfiguracaoEngajamento, Engajamento
from aplicacoes.eventos.models import Evento, Participacao
from aplicacoes.nucleo.models import LogAlteracao, Perfil


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'usuario{n}')
    first_name = factory.Faker('first_name', locale='pt_BR')
    last_name = factory.Faker('last_name', locale='pt_BR')
    email = factory.LazyAttribute(lambda o: f'{o.username}@exemplo.gov.br')
    password = factory.PostGenerationMethodCall('set_password', 'senha123')
    is_active = True


class PerfilFactory(DjangoModelFactory):
    class Meta:
        model = Perfil

    usuario = factory.SubFactory(UserFactory)
    tipo = Perfil.TipoPerfil.VISUALIZADOR


class PessoaFactory(DjangoModelFactory):
    class Meta:
        model = Pessoa

    nome = factory.Faker('name', locale='pt_BR')
    email = factory.LazyAttribute(lambda o: f'{o.nome.lower().replace(" ", ".")}@exemplo.gov.br')
    tipo = Pessoa.TipoPessoa.PREFEITO
    genero = Pessoa.Genero.NAO_INFORMADO
    ativo = True


class MunicipioFactory(DjangoModelFactory):
    class Meta:
        model = Municipio

    nome = factory.Faker('city', locale='pt_BR')
    uf = 'SP'
    codigo_ibge = factory.Sequence(lambda n: 3500000 + n)
    populacao = factory.Faker('random_int', min=50000, max=5000000)
    regiao = Municipio.Regiao.SUDESTE
    eh_capital = False
    associado_fnp = True
    latitude = factory.Faker('latitude')
    longitude = factory.Faker('longitude')


class VinculoMunicipioFactory(DjangoModelFactory):
    class Meta:
        model = VinculoMunicipio

    pessoa = factory.SubFactory(PessoaFactory)
    municipio = factory.SubFactory(MunicipioFactory)
    papel = VinculoMunicipio.Papel.PREFEITO
    vigente = True


class PautaFactory(DjangoModelFactory):
    class Meta:
        model = Pauta

    nome = factory.Sequence(lambda n: f'Pauta {n}')
    ativa = True


class AdimplenciaFactory(DjangoModelFactory):
    class Meta:
        model = Adimplencia

    municipio = factory.SubFactory(MunicipioFactory)
    ano_referencia = 2026
    status = Adimplencia.Status.ADIMPLENTE
    valor_devido = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
    valor_pago = factory.LazyAttribute(lambda o: o.valor_devido)


class EventoFactory(DjangoModelFactory):
    class Meta:
        model = Evento

    titulo = factory.Faker('sentence', nb_words=5, locale='pt_BR')
    tipo = Evento.TipoEvento.REUNIAO_GERAL
    modalidade = Evento.Modalidade.PRESENCIAL
    data_inicio = factory.Faker('date_this_year')
    local = factory.Faker('city', locale='pt_BR')
    pontos_presencial = 10
    pontos_online = 5
    pontos_palestrante_bonus = 5
    pontos_organizador_bonus = 5


class ParticipacaoFactory(DjangoModelFactory):
    class Meta:
        model = Participacao

    pessoa = factory.SubFactory(PessoaFactory)
    evento = factory.SubFactory(EventoFactory)
    municipio = factory.SubFactory(MunicipioFactory)
    forma_participacao = Participacao.FormaParticipacao.PRESENCIAL
    papel_no_evento = Participacao.PapelNoEvento.PARTICIPANTE
    confirmado = True


class ConfiguracaoEngajamentoFactory(DjangoModelFactory):
    class Meta:
        model = ConfiguracaoEngajamento

    bienio_atual = '2025-2026'
    meta_bienio = 200
    fator_decaimento = 0.70
    penalidade_inadimplente = 0.30
    penalidade_parcial = 0.15


class EngajamentoFactory(DjangoModelFactory):
    class Meta:
        model = Engajamento

    municipio = factory.SubFactory(MunicipioFactory)
    bienio = '2025-2026'


class LogAlteracaoFactory(DjangoModelFactory):
    class Meta:
        model = LogAlteracao

    usuario = factory.SubFactory(UserFactory)
    acao = LogAlteracao.TipoAcao.CRIACAO
    modelo = 'Pessoa'
    objeto_id = factory.Faker('uuid4')
    objeto_repr = factory.Faker('name', locale='pt_BR')
