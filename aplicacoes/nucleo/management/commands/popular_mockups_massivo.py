"""Popula o banco com mockups massivos para demos visuais ricas.

Acrescenta (idempotente, todos com get_or_create):
- ~50 municipios extra (alem das 57 do popular_mapa_brasil)
- ~30 espacos de dialogo (instancias)
- ~30 projetos
- ~25 missoes
- ~50 atividades
- adimplencia para todos os municipios populados

Uso:
    python manage.py popular_mockups_massivo
    python manage.py popular_mockups_massivo --limpar-fake  # apaga so os fake
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from aplicacoes.adimplencia.models import Adimplencia
from aplicacoes.atividades.models import Atividade
from aplicacoes.cadastro.models import Municipio, Pessoa
from aplicacoes.instancias.models import Instancia
from aplicacoes.missoes.models import Missao
from aplicacoes.projetos.models import Projeto


# ---------------------------------------------------------------------------
# Dados curados
# ---------------------------------------------------------------------------
MUNICIPIOS_EXTRA = [
    # (codigo_ibge, nome, uf, regiao, lat, lng, populacao, eh_capital, associado_fnp)
    # NORTE
    (1302108, 'Itacoatiara', 'AM', 'norte', -3.1430, -58.4434, 100000, False, False),
    (1100130, 'Cacoal', 'RO', 'norte', -11.4385, -61.4474, 90000, False, False),
    (1200401, 'Cruzeiro do Sul', 'AC', 'norte', -7.6307, -72.6735, 88000, False, False),
    (1721000, 'Araguaina', 'TO', 'norte', -7.1911, -48.2086, 175000, False, True),
    (1502152, 'Maraba', 'PA', 'norte', -5.3686, -49.1182, 287000, False, True),
    (1505536, 'Parauapebas', 'PA', 'norte', -6.0675, -49.9019, 220000, False, True),
    # NORDESTE
    (2304400, 'Caucaia', 'CE', 'nordeste', -3.7368, -38.6531, 365000, False, True),
    (2305001, 'Maracanau', 'CE', 'nordeste', -3.8717, -38.6256, 224000, False, False),
    (2207702, 'Parnaiba', 'PI', 'nordeste', -2.9047, -41.7762, 153000, False, False),
    (2101400, 'Caxias', 'MA', 'nordeste', -4.8587, -43.3556, 165000, False, False),
    (2403301, 'Caico', 'RN', 'nordeste', -6.4644, -37.0975, 64000, False, False),
    (2504009, 'Cabedelo', 'PB', 'nordeste', -6.9810, -34.8338, 67000, False, True),
    (2611606, 'Jaboatao dos Guararapes', 'PE', 'nordeste', -8.1130, -35.0150, 706000, False, True),
    (2613404, 'Olinda', 'PE', 'nordeste', -7.9925, -34.8511, 391000, False, True),
    (2802908, 'Itabaiana', 'SE', 'nordeste', -10.6883, -37.4256, 95000, False, False),
    (2929206, 'Vitoria da Conquista', 'BA', 'nordeste', -14.8615, -40.8442, 341000, False, True),
    (2918407, 'Ilheus', 'BA', 'nordeste', -14.7889, -39.0494, 159000, False, False),
    # CENTRO-OESTE
    (5208707, 'Aparecida de Goiania', 'GO', 'centro_oeste', -16.8235, -49.2438, 590000, False, True),
    (5208400, 'Anapolis', 'GO', 'centro_oeste', -16.3267, -48.9527, 391000, False, True),
    (5103403, 'Rondonopolis', 'MT', 'centro_oeste', -16.4672, -54.6378, 230000, False, False),
    (5101258, 'Sinop', 'MT', 'centro_oeste', -11.8606, -55.5028, 142000, False, False),
    (5007307, 'Tres Lagoas', 'MS', 'centro_oeste', -20.7849, -51.7007, 124000, False, False),
    # SUDESTE
    (3530607, 'Osasco', 'SP', 'sudeste', -23.5326, -46.7916, 700000, False, True),
    (3548708, 'Sao Bernardo do Campo', 'SP', 'sudeste', -23.6896, -46.5654, 845000, False, True),
    (3547809, 'Sao Caetano do Sul', 'SP', 'sudeste', -23.6181, -46.5527, 162000, False, True),
    (3527207, 'Maua', 'SP', 'sudeste', -23.6678, -46.4613, 488000, False, False),
    (3534401, 'Praia Grande', 'SP', 'sudeste', -24.0073, -46.4035, 330000, False, True),
    (3525904, 'Jundiai', 'SP', 'sudeste', -23.1864, -46.8842, 423000, False, True),
    (3543907, 'Rio Claro', 'SP', 'sudeste', -22.4106, -47.5614, 211000, False, False),
    (3303609, 'Nova Iguacu', 'RJ', 'sudeste', -22.7592, -43.4500, 821000, False, False),
    (3300456, 'Belford Roxo', 'RJ', 'sudeste', -22.7639, -43.3993, 514000, False, False),
    (3302007, 'Duque de Caxias', 'RJ', 'sudeste', -22.7858, -43.3115, 924000, False, True),
    (3303906, 'Petropolis', 'RJ', 'sudeste', -22.5051, -43.1786, 306000, False, False),
    (3171303, 'Uberaba', 'MG', 'sudeste', -19.7472, -47.9381, 333000, False, True),
    (3136702, 'Juiz de Fora', 'MG', 'sudeste', -21.7642, -43.3503, 568000, False, True),
    (3148004, 'Sete Lagoas', 'MG', 'sudeste', -19.4569, -44.2477, 240000, False, False),
    (3144805, 'Pocos de Caldas', 'MG', 'sudeste', -21.7869, -46.5614, 165000, False, False),
    (3205200, 'Cariacica', 'ES', 'sudeste', -20.2632, -40.4163, 386000, False, True),
    # SUL
    (4106407, 'Cascavel', 'PR', 'sul', -24.9555, -53.4552, 332000, False, True),
    (4108304, 'Foz do Iguacu', 'PR', 'sul', -25.5478, -54.5882, 258000, False, True),
    (4111407, 'Guarapuava', 'PR', 'sul', -25.3935, -51.4628, 182000, False, False),
    (4128203, 'Toledo', 'PR', 'sul', -24.7245, -53.7414, 142000, False, False),
    (4214203, 'Itajai', 'SC', 'sul', -26.9077, -48.6614, 224000, False, True),
    (4209102, 'Chapeco', 'SC', 'sul', -27.0961, -52.6188, 220000, False, True),
    (4204004, 'Criciuma', 'SC', 'sul', -28.6779, -49.3702, 215000, False, False),
    (4313409, 'Novo Hamburgo', 'RS', 'sul', -29.6783, -51.1306, 248000, False, True),
    (4308201, 'Gravatai', 'RS', 'sul', -29.9442, -50.9919, 277000, False, False),
    (4318705, 'Sao Leopoldo', 'RS', 'sul', -29.7600, -51.1472, 240000, False, True),
    (4313904, 'Passo Fundo', 'RS', 'sul', -28.2640, -52.4067, 207000, False, False),
    (4308102, 'Gramado', 'RS', 'sul', -29.3742, -50.8767, 36000, False, True),
]


INSTANCIAS_MOCKUP = [
    # (nome, origem, forma, categoria, status, periodicidade)
    ('Comissão de Saúde Municipal', 'interna', 'comissao', 'principal', 'em_funcionamento', 'mensal'),
    ('Comissão de Educação', 'interna', 'comissao', 'principal', 'em_funcionamento', 'mensal'),
    ('Comissão de Mobilidade Urbana', 'interna', 'comissao', 'principal', 'em_funcionamento', 'bimestral'),
    ('Comissão de Cultura e Turismo', 'interna', 'comissao', 'principal', 'em_funcionamento', 'mensal'),
    ('Comissão de Segurança Pública', 'interna', 'comissao', 'principal', 'em_funcionamento', 'mensal'),
    ('Comissão de Sustentabilidade e Meio Ambiente', 'interna', 'comissao', 'principal', 'em_funcionamento', 'bimestral'),
    ('Comissão de Habitação Popular', 'interna', 'comissao', 'principal', 'em_construcao', 'trimestral'),
    ('Comissão de Assistência Social', 'interna', 'comissao', 'principal', 'em_funcionamento', 'mensal'),
    ('Comissão de Finanças e Orçamento', 'interna', 'comissao', 'principal', 'em_funcionamento', 'mensal'),
    ('Comissão de Inovação e Tecnologia', 'interna', 'comissao', 'principal', 'em_funcionamento', 'bimestral'),
    ('Fórum Nacional de Prefeitos das Capitais', 'interna', 'forum', 'principal', 'em_funcionamento', 'trimestral'),
    ('Fórum de Cidades Inteligentes', 'interna', 'forum', 'principal', 'em_funcionamento', 'bimestral'),
    ('Fórum Brasileiro de Mudança Climática', 'externa', 'forum', 'principal', 'em_funcionamento', 'semestral'),
    ('Fórum de Saúde Coletiva', 'interna', 'forum', 'principal', 'em_funcionamento', 'mensal'),
    ('Fórum de Desenvolvimento Regional', 'interna', 'forum', 'principal', 'em_funcionamento', 'trimestral'),
    ('Conselho Nacional de Política Urbana', 'externa', 'com_representacao', 'principal', 'em_funcionamento', 'bimestral'),
    ('Conselho Nacional de Saúde', 'externa', 'com_representacao', 'principal', 'em_funcionamento', 'mensal'),
    ('Conselho Nacional dos Direitos da Criança', 'externa', 'com_representacao', 'principal', 'em_funcionamento', 'bimestral'),
    ('Conselho Nacional de Educação', 'externa', 'com_representacao', 'principal', 'em_funcionamento', 'bimestral'),
    ('Rede Brasileira de Cidades Saudáveis', 'externa', 'com_representacao', 'principal', 'em_funcionamento', 'semestral'),
    ('Rede de Mulheres na Política Municipal', 'interna', 'forum', 'principal', 'em_funcionamento', 'trimestral'),
    ('GT de Gestão Fiscal Municipal', 'interna', 'comissao', 'secundaria', 'em_funcionamento', 'mensal'),
    ('GT de Saneamento Básico', 'interna', 'comissao', 'secundaria', 'em_funcionamento', 'bimestral'),
    ('GT de Defesa Civil', 'interna', 'comissao', 'secundaria', 'em_funcionamento', 'trimestral'),
    ('GT de Energia e Eficiência Energética', 'interna', 'comissao', 'secundaria', 'em_construcao', 'em_definicao'),
    ('Comitê de Diversidade e Inclusão', 'interna', 'comissao', 'principal', 'em_construcao', 'trimestral'),
    ('Comitê de Pacto Federativo', 'interna', 'comissao', 'principal', 'em_funcionamento', 'bimestral'),
    ('Associação dos Municípios do Sul', 'externa', 'sem_representacao', 'principal', 'em_funcionamento', 'semestral'),
    ('Aliança Nacional de Municípios pelo Clima', 'externa', 'com_representacao', 'principal', 'em_funcionamento', 'trimestral'),
    ('Fórum Brasileiro de Segurança Pública', 'externa', 'forum', 'principal', 'em_funcionamento', 'semestral'),
]


PROJETOS_MOCKUP = [
    # (nome, status, fonte_recurso, valor_orcado, dias_inicio_offset, dias_fim_offset)
    ('Cidades Inteligentes — Fase Piloto', 'em_andamento', 'parceria', 1500000, -180, 365),
    ('Capacitação de Gestores em LGPD', 'em_andamento', 'proprio', 250000, -90, 180),
    ('Programa Federativo de Saneamento', 'planejamento', 'convenio', 3500000, 30, 730),
    ('Plataforma Federativa de Dados Municipais', 'em_andamento', 'parceria', 800000, -120, 540),
    ('Mapa Brasileiro do Clima Municipal', 'concluido', 'internacional', 600000, -540, -30),
    ('Diagnóstico Nacional de Mobilidade Urbana', 'em_andamento', 'emenda', 1200000, -60, 365),
    ('Rede Nacional de Cidades pela Paz', 'em_andamento', 'proprio', 450000, -270, 180),
    ('Observatório de Políticas Municipais', 'planejamento', 'parceria', 950000, 60, 540),
    ('Capacitação em Compras Públicas', 'em_andamento', 'convenio', 380000, -90, 270),
    ('Caravana Federativa 2026', 'em_andamento', 'proprio', 2000000, -30, 240),
    ('Diálogo Municipal pela Educação Integral', 'em_andamento', 'parceria', 720000, -150, 450),
    ('Pacto pela Primeira Infância', 'em_andamento', 'convenio', 1100000, -180, 540),
    ('Inovação na Gestão Tributária Municipal', 'planejamento', 'parceria', 540000, 0, 365),
    ('Cidades 30 — Velocidades Seguras', 'em_andamento', 'internacional', 320000, -120, 240),
    ('Habitação Social com ESG', 'pausado', 'parceria', 1800000, -360, 540),
    ('Plataforma Nacional de Defesa Civil', 'em_andamento', 'emenda', 890000, -60, 365),
    ('Estudo Comparado de Receitas Próprias', 'concluido', 'proprio', 180000, -720, -180),
    ('Selo Cidade Amiga do Idoso', 'em_andamento', 'parceria', 240000, -200, 180),
    ('Diagnóstico de Cultura Municipal', 'em_andamento', 'convenio', 410000, -90, 270),
    ('Energia Solar para Equipamentos Públicos', 'em_andamento', 'internacional', 1650000, -150, 540),
    ('Programa de Aceleração de Startups Govtech', 'em_andamento', 'parceria', 780000, -90, 365),
    ('Bem-Estar Animal nas Cidades', 'planejamento', 'proprio', 220000, 30, 365),
    ('Selo Cidade Empreendedora', 'em_andamento', 'parceria', 380000, -120, 240),
    ('Pacto pela Educação Antirracista', 'em_andamento', 'convenio', 540000, -180, 365),
    ('Mapa Brasileiro de Hortas Urbanas', 'em_andamento', 'internacional', 290000, -150, 180),
    ('Rede de Apoio a Pessoas em Situação de Rua', 'em_andamento', 'emenda', 870000, -90, 540),
    ('Pesquisa Nacional de Tributação Municipal', 'planejamento', 'proprio', 320000, 60, 365),
    ('Inteligência Artificial na Gestão Pública', 'em_andamento', 'parceria', 1300000, -30, 540),
    ('Caravana FNP Norte e Nordeste', 'concluido', 'proprio', 850000, -390, -120),
    ('Conectividade nas Escolas Municipais', 'em_andamento', 'convenio', 1750000, -90, 540),
]


MISSOES_MOCKUP = [
    # (titulo, tipo, status, cidade, pais, dias_offset)
    ('COP — Reunião de Prefeitos pela Ação Climática', 'internacional', 'realizada', 'Belém', 'Brasil', -90),
    ('Smart City Expo World Congress', 'internacional', 'realizada', 'Barcelona', 'Espanha', -180),
    ('C40 Mayors Summit', 'internacional', 'realizada', 'Buenos Aires', 'Argentina', -300),
    ('Missão Técnica — Habitação Social', 'internacional', 'realizada', 'Bogotá', 'Colômbia', -240),
    ('Encontro Iberoamericano de Cidades Educadoras', 'internacional', 'realizada', 'Cascais', 'Portugal', -150),
    ('Visita Técnica — Mobilidade Urbana', 'internacional', 'realizada', 'Medellín', 'Colômbia', -120),
    ('OECD Forum on Urban Resilience', 'internacional', 'planejada', 'Paris', 'França', 60),
    ('Mercocidades — Cúpula 2026', 'internacional', 'planejada', 'Montevidéu', 'Uruguai', 90),
    ('UCLG Congress', 'internacional', 'em_andamento', 'Daejeon', 'Coreia do Sul', -5),
    ('Encontro Latino-americano de Saneamento', 'internacional', 'planejada', 'Cidade do México', 'México', 120),
    ('Visita à Itaipu Binacional — Energia Limpa', 'nacional', 'realizada', 'Foz do Iguaçu', 'Brasil', -45),
    ('Diálogo Federativo no Congresso Nacional', 'nacional', 'realizada', 'Brasília', 'Brasil', -30),
    ('Encontro Regional do Nordeste', 'nacional', 'realizada', 'Recife', 'Brasil', -60),
    ('Encontro Regional do Sul', 'nacional', 'realizada', 'Curitiba', 'Brasil', -75),
    ('Encontro Regional do Norte', 'nacional', 'realizada', 'Manaus', 'Brasil', -100),
    ('Visita Técnica à Embrapa', 'nacional', 'realizada', 'Campinas', 'Brasil', -200),
    ('Diálogo com STF sobre Pacto Federativo', 'nacional', 'realizada', 'Brasília', 'Brasil', -15),
    ('Encontro com Presidência da República', 'nacional', 'realizada', 'Brasília', 'Brasil', -25),
    ('Missão Conjunta com TCU', 'nacional', 'planejada', 'Brasília', 'Brasil', 45),
    ('Visita às Cidades do Vale do Silício Brasileiro', 'nacional', 'planejada', 'São Carlos', 'Brasil', 75),
    ('Encontro Nacional de Secretários de Fazenda', 'nacional', 'em_andamento', 'Brasília', 'Brasil', 0),
    ('Encontro Internacional de Cidades pela Paz', 'internacional', 'planejada', 'Genebra', 'Suíça', 180),
    ('Visita Técnica — Política de Mudança Climática', 'internacional', 'realizada', 'Quito', 'Equador', -210),
    ('FIM da Conferência da OEA — Diálogo Federativo', 'internacional', 'planejada', 'Washington', 'EUA', 150),
    ('Encontro com Banco Mundial — Crédito Verde', 'internacional', 'realizada', 'Washington', 'EUA', -270),
]


# ---------------------------------------------------------------------------
# Comando
# ---------------------------------------------------------------------------
class Command(BaseCommand):
    help = 'Popula mockups massivos: municipios extra, instancias, projetos, missoes, atividades.'

    def add_arguments(self, parser):
        parser.add_argument('--limpar-fake', action='store_true',
                            help='Apaga registros criados por seeds (sem afetar dados reais).')

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(42)

        # 1. MUNICIPIOS extra
        self.stdout.write('Adicionando municípios extra...')
        n_municipios = 0
        for cod, nome, uf, regiao, lat, lng, pop, capital, assoc in MUNICIPIOS_EXTRA:
            _, novo = Municipio.objects.get_or_create(
                codigo_ibge=cod,
                defaults={
                    'nome': nome, 'uf': uf, 'regiao': regiao,
                    'latitude': lat, 'longitude': lng, 'populacao': pop,
                    'eh_capital': capital, 'associado_fnp': assoc,
                },
            )
            if novo:
                n_municipios += 1

        # 2. ADIMPLENCIA para todos os municipios (que ainda nao tem)
        self.stdout.write('Cadastrando adimplência para municípios...')
        ano = date.today().year
        n_adim = 0
        status_dist = ['adimplente'] * 60 + ['parcial'] * 25 + ['inadimplente'] * 15
        for m in Municipio.objects.all():
            if Adimplencia.objects.filter(municipio=m, ano_referencia=ano).exists():
                continue
            status = random.choice(status_dist)
            valor_devido = round(m.populacao * 0.05, 2)
            valor_pago = {
                'adimplente': valor_devido,
                'parcial': round(valor_devido * 0.5, 2),
                'inadimplente': 0,
            }[status]
            Adimplencia.objects.create(
                municipio=m, ano_referencia=ano,
                status=status, valor_devido=valor_devido, valor_pago=valor_pago,
            )
            n_adim += 1

        # 3. INSTANCIAS
        self.stdout.write('Criando espaços de diálogo...')
        n_instancias = 0
        for nome, origem, forma, cat, status, period in INSTANCIAS_MOCKUP:
            _, novo = Instancia.objects.get_or_create(
                nome=nome,
                defaults={
                    'origem': origem, 'forma': forma, 'categoria': cat,
                    'status': status, 'periodicidade_reunioes': period,
                },
            )
            if novo:
                n_instancias += 1

        # 4. PROJETOS
        self.stdout.write('Criando projetos...')
        n_projetos = 0
        for nome, status, fonte, valor, di_off, df_off in PROJETOS_MOCKUP:
            _, novo = Projeto.objects.get_or_create(
                nome=nome,
                defaults={
                    'status': status, 'fonte_recurso': fonte, 'valor_orcado': valor,
                    'data_inicio': date.today() + timedelta(days=di_off),
                    'data_fim_previsto': date.today() + timedelta(days=df_off),
                },
            )
            if novo:
                n_projetos += 1

        # 5. MISSOES
        self.stdout.write('Criando missões...')
        n_missoes = 0
        for titulo, tipo, status, cidade, pais, off in MISSOES_MOCKUP:
            data_inicio = date.today() + timedelta(days=off)
            data_fim = data_inicio + timedelta(days=random.randint(2, 7))
            _, novo = Missao.objects.get_or_create(
                titulo=titulo,
                defaults={
                    'tipo': tipo, 'status': status,
                    'cidade': cidade, 'pais': pais,
                    'data_inicio': data_inicio, 'data_fim': data_fim,
                },
            )
            if novo:
                n_missoes += 1

        # 6. ATIVIDADES — 2-3 por instancia ativa
        self.stdout.write('Criando atividades das instâncias...')
        n_atividades = 0
        ativas = Instancia.objects.filter(status='em_funcionamento')
        for inst in ativas:
            quantas = random.randint(1, 3)
            for i in range(quantas):
                off = random.randint(-60, 30)
                data_reuniao = date.today() + timedelta(days=off)
                # Status realista: passado=realizada, futuro=agendada
                if off < -7:
                    status = 'realizada'
                elif off < 0:
                    status = random.choice(['realizada', 'adiada'])
                else:
                    status = 'agendada'
                _, novo = Atividade.objects.get_or_create(
                    instancia=inst, data_reuniao=data_reuniao,
                    defaults={
                        'formato': random.choice(['presencial', 'virtual', 'hibrida']),
                        'tipo_calendario': 'ordinaria' if i == 0 else random.choice(['ordinaria', 'extraordinaria']),
                        'status': status,
                        'possui_pauta': status in ('realizada', 'adiada'),
                        'possui_ata': status == 'realizada',
                        'possui_lista_presenca': status == 'realizada',
                    },
                )
                if novo:
                    n_atividades += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nMockups criados:\n'
            f'  Municípios:    {n_municipios}\n'
            f'  Adimplências:  {n_adim}\n'
            f'  Instâncias:    {n_instancias}\n'
            f'  Projetos:      {n_projetos}\n'
            f'  Missões:       {n_missoes}\n'
            f'  Atividades:    {n_atividades}'
        ))
        self.stdout.write(self.style.SUCCESS(
            f'\nTotais no banco:\n'
            f'  Municípios:    {Municipio.objects.count()}\n'
            f'  Instâncias:    {Instancia.objects.count()}\n'
            f'  Projetos:      {Projeto.objects.count()}\n'
            f'  Missões:       {Missao.objects.count()}\n'
            f'  Atividades:    {Atividade.objects.count()}'
        ))
