"""Management command para popular as novas categorias com dados fictícios.

Cria 20+ registros de cada categoria nova (Instância, Projeto, Missão,
Atividade) além de Eventos extras e mais Pessoas para enriquecer o cenário
visual de demonstração. Todos os dados são inventados — nada de identidades
reais. Reexecutar é seguro: usa get_or_create na maioria dos casos.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from django.contrib.contenttypes.models import ContentType

from aplicacoes.atividades.models import Atividade
from aplicacoes.cadastro.models import Municipio, Pessoa, VinculoMunicipio
from aplicacoes.documentos.models import Documento
from aplicacoes.eventos.models import Evento, Participacao
from aplicacoes.instancias.models import Instancia, Representacao
from aplicacoes.missoes.models import MembroDelegacao, Missao
from aplicacoes.projetos.models import Projeto


# Nomes fictícios de espaços de diálogo (mistura de internos e externos)
INSTANCIAS_DADOS = [
    ('Conselho Nacional de Política Urbana', 'externa', 'comissao', 'principal'),
    ('Fórum FNP de Saúde Municipal', 'interna', 'forum', 'principal'),
    ('Comissão de Mudanças Climáticas', 'interna', 'comissao', 'principal'),
    ('GT Mobilidade Urbana Sustentável', 'interna', 'com_representacao', 'secundaria'),
    ('Conselho Nacional de Assistência Social', 'externa', 'comissao', 'principal'),
    ('Fórum de Cultura das Cidades', 'interna', 'forum', 'principal'),
    ('Comitê Interfederativo do SUS', 'externa', 'comissao', 'principal'),
    ('Rede Brasileira de Cidades Saudáveis', 'externa', 'sem_representacao', 'principal'),
    ('Comissão Permanente de Educação', 'interna', 'comissao', 'principal'),
    ('GT Segurança Pública Municipal', 'interna', 'com_representacao', 'secundaria'),
    ('Conselho de Direitos da Criança', 'externa', 'comissao', 'principal'),
    ('Fórum de Desenvolvimento Econômico', 'interna', 'forum', 'principal'),
    ('Conselho Nacional de Habitação', 'externa', 'comissao', 'principal'),
    ('GT Cidades Inteligentes', 'interna', 'com_representacao', 'secundaria'),
    ('Comissão de Saneamento Básico', 'interna', 'comissao', 'principal'),
    ('Fórum FNP de Inovação Pública', 'interna', 'forum', 'principal'),
    ('Conselho Nacional do Meio Ambiente', 'externa', 'comissao', 'principal'),
    ('Comitê Gestor de Resíduos Sólidos', 'externa', 'comissao', 'secundaria'),
    ('Fórum de Igualdade Racial', 'interna', 'forum', 'principal'),
    ('Comissão de Turismo e Patrimônio', 'interna', 'comissao', 'principal'),
    ('Rede Internacional de Cidades pelo Clima', 'externa', 'sem_representacao', 'principal'),
]

# Projetos fictícios
PROJETOS_DADOS = [
    ('Capacita Cidades 2026', 'Programa de capacitação para gestores municipais.'),
    ('Plano Diretor Verde', 'Apoio à revisão de planos diretores com critérios climáticos.'),
    ('Inova SUS Municipal', 'Modernização da gestão de saúde nas capitais.'),
    ('Mobilidade Limpa', 'Promoção de transporte público elétrico em grandes cidades.'),
    ('Habitação Acessível', 'Articulação para programas habitacionais nos municípios.'),
    ('Educação Conectada', 'Conectividade em escolas municipais.'),
    ('Resíduos Zero', 'Apoio à gestão de resíduos sólidos urbanos.'),
    ('Cidades Antifragilidade', 'Preparação para eventos climáticos extremos.'),
    ('Segurança Cidadã', 'Compartilhamento de boas práticas em segurança municipal.'),
    ('Saneamento Total 2030', 'Articulação pela universalização do saneamento.'),
    ('Cultura nas Praças', 'Fomento a programações culturais municipais.'),
    ('Empreender Local', 'Apoio a políticas de fomento ao empreendedorismo.'),
    ('Cidades Acessíveis', 'Inclusão urbana para pessoas com deficiência.'),
    ('Juventude e Cidades', 'Políticas municipais para jovens.'),
    ('Diálogo Federativo Climático', 'Coordenação federativa para metas climáticas.'),
    ('Centros Históricos Vivos', 'Revitalização de centros urbanos históricos.'),
    ('Smart Cities Brasil', 'Plataforma para indicadores de cidades inteligentes.'),
    ('Praça Cidadã Digital', 'Wi-Fi público e serviços digitais em praças.'),
    ('Resgate da Atenção Básica', 'Fortalecimento da APS nos municípios.'),
    ('Cooperação Internacional FNP', 'Articulação com redes globais de cidades.'),
]

# Missões fictícias
MISSOES_DADOS = [
    ('Missão FNP a Bogotá — Mobilidade Urbana', 'internacional', 'Colômbia', 'Bogotá'),
    ('Visita Técnica a Medellín', 'internacional', 'Colômbia', 'Medellín'),
    ('Missão Paris — COP30 Preparatória', 'internacional', 'França', 'Paris'),
    ('Encontro Mercocidades em Buenos Aires', 'internacional', 'Argentina', 'Buenos Aires'),
    ('Missão Tóquio — Smart Cities', 'internacional', 'Japão', 'Tóquio'),
    ('Visita a Barcelona — Superquadras', 'internacional', 'Espanha', 'Barcelona'),
    ('Cooperação com Lisboa', 'internacional', 'Portugal', 'Lisboa'),
    ('Missão a Nova York — ONU Habitat', 'internacional', 'Estados Unidos', 'Nova York'),
    ('Encontro Andino em Quito', 'internacional', 'Equador', 'Quito'),
    ('Visita técnica a Curitiba', 'nacional', 'Brasil', 'Curitiba'),
    ('Missão Manaus — Adaptação Climática', 'nacional', 'Brasil', 'Manaus'),
    ('Reunião Estratégica em Brasília', 'nacional', 'Brasil', 'Brasília'),
    ('Visita a Recife — Habitação', 'nacional', 'Brasil', 'Recife'),
    ('Encontro Regional Sul — Porto Alegre', 'nacional', 'Brasil', 'Porto Alegre'),
    ('Missão Belém — COP30 Logística', 'nacional', 'Brasil', 'Belém'),
    ('Visita técnica Goiânia — Saúde', 'nacional', 'Brasil', 'Goiânia'),
    ('Encontro Nordeste em Fortaleza', 'nacional', 'Brasil', 'Fortaleza'),
    ('Missão Florianópolis — Inovação', 'nacional', 'Brasil', 'Florianópolis'),
    ('Reunião com governadores em São Paulo', 'nacional', 'Brasil', 'São Paulo'),
    ('Missão Vitória — Mobilidade', 'nacional', 'Brasil', 'Vitória'),
]

# Eventos fictícios extras
EVENTOS_DADOS = [
    ('Seminário Cidades 2026', 'seminario', 'articulacao_politica', 'consultivo'),
    ('Workshop de Indicadores Climáticos', 'workshop', 'formacao', 'formativo'),
    ('Congresso Brasileiro de Municípios', 'congresso', 'tomada_decisao', 'deliberativo'),
    ('Assembléia FNP 2026', 'assembleia_geral', 'tomada_decisao', 'deliberativo'),
    ('Conferência Nacional de Saúde Municipal', 'conferencia', 'incidencia_institucional', 'consultivo'),
    ('GT Mobilidade — Encontro de outubro', 'grupos_trabalho', 'tomada_decisao', 'deliberativo'),
    ('Audiência Pública — Saneamento', 'audiencia', 'incidencia_institucional', 'consultivo'),
    ('Workshop de Inovação Pública', 'workshop', 'formacao', 'formativo'),
    ('Seminário de Habitação Popular', 'seminario', 'articulacao_politica', 'consultivo'),
    ('Congresso de Cultura Municipal', 'congresso', 'articulacao_politica', 'deliberativo'),
    ('Reunião de Projeto — Capacita Cidades', 'reuniao_projeto', 'formacao', 'formativo'),
    ('Webinar de Mudanças Climáticas', 'webinar', 'formacao', 'formativo'),
    ('Fórum de Mulheres na Gestão', 'forum', 'articulacao_politica', 'consultivo'),
    ('Conferência Internacional de Cidades', 'conferencia', 'articulacao_politica', 'consultivo'),
    ('Comissão Permanente — Segurança', 'comissoes', 'tomada_decisao', 'deliberativo'),
    ('Workshop de Resíduos Sólidos', 'workshop', 'formacao', 'formativo'),
    ('Seminário Smart Cities Brasil', 'seminario', 'formacao', 'consultivo'),
    ('Audiência Pública — Mobilidade', 'audiencia', 'incidencia_institucional', 'consultivo'),
    ('Reunião Geral da FNP — Maio', 'reuniao_geral', 'tomada_decisao', 'deliberativo'),
    ('Workshop de Cooperação Internacional', 'workshop', 'formacao', 'formativo'),
]

# Pessoas extras — nomes inventados, mistura de prefeitos, secretários e internos
PESSOAS_EXTRAS = [
    ('Ana Carolina Souza', 'prefeito'),
    ('Pedro Henrique Silva', 'secretario'),
    ('Marina Lopes Ferreira', 'assessor'),
    ('Roberto Oliveira Lima', 'prefeito'),
    ('Camila Rodrigues Pinto', 'secretario'),
    ('João Mateus Almeida', 'interno'),
    ('Beatriz Marcondes Costa', 'prefeito'),
    ('Lucas Fernandes Reis', 'secretario'),
    ('Fernanda Vieira Castro', 'interno'),
    ('Gabriel Santos Moreira', 'assessor'),
    ('Larissa Carvalho Dias', 'prefeito'),
    ('Diego Martins Cunha', 'secretario'),
    ('Patricia Albuquerque Ramos', 'interno'),
    ('Rafael Cordeiro Nunes', 'prefeito'),
    ('Juliana Mendes Tavares', 'secretario'),
    ('Marcelo Barbosa Pinheiro', 'assessor'),
    ('Tatiana Ribeiro Pereira', 'prefeito'),
    ('Felipe Azevedo Monteiro', 'secretario'),
    ('Renata Cavalcanti Lopes', 'interno'),
    ('Bruno Teixeira Machado', 'vice_prefeito'),
    ('Aline Moura Cardoso', 'secretario'),
    ('Eduardo Pacheco Freitas', 'assessor'),
    ('Sofia Vasconcelos Andrade', 'prefeito'),
    ('Henrique Borges Caldas', 'vereador'),
    ('Letícia Magalhães Coelho', 'secretario'),
    ('Vinícius Duarte Siqueira', 'interno'),
    ('Mariana Galvão Pinto', 'assessor'),
    ('Thiago Macedo Carvalho', 'prefeito'),
    ('Isabela Antunes Brito', 'secretario'),
    ('Caio Bezerra Marinho', 'interno'),
]

GENEROS = ['masculino', 'feminino', 'feminino', 'masculino', 'outro']
PARTIDOS = ['PT', 'PSDB', 'MDB', 'PL', 'PSD', 'PP', 'União', 'Republicanos', 'Cidadania', '']


class Command(BaseCommand):
    """Popula as categorias novas (instâncias, projetos, missões, atividades) com dados fictícios."""

    help = 'Cria 20+ registros fictícios em cada nova categoria + pessoas extras para demonstração.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Remove dados das novas categorias antes de popular (não afeta Pessoas/Municípios).',
        )

    def handle(self, *args, **options):
        if options['limpar']:
            self.stdout.write('Limpando categorias...')
            Atividade.objects.all().delete()
            Representacao.objects.all().delete()
            MembroDelegacao.objects.all().delete()
            Missao.objects.all().delete()
            Projeto.objects.all().delete()
            Instancia.objects.all().delete()

        municipios = list(Municipio.objects.all())
        if not municipios:
            self.stdout.write(self.style.ERROR(
                'Nenhum município encontrado. Rode `popular_mockup` primeiro.'
            ))
            return

        # 1. Pessoas extras
        self.stdout.write('Criando pessoas extras...')
        pessoas_criadas = self._criar_pessoas_extras(municipios)
        self.stdout.write(f'  {pessoas_criadas} pessoas novas')

        todas_pessoas = list(Pessoa.objects.filter(ativo=True))
        pessoas_internas = [p for p in todas_pessoas if p.tipo == Pessoa.TipoPessoa.INTERNO]

        # 2. Instâncias
        self.stdout.write('Criando instâncias...')
        instancias = self._criar_instancias(pessoas_internas)
        self.stdout.write(f'  {len(instancias)} instâncias')

        # 3. Representações
        self.stdout.write('Criando representações em instâncias...')
        n_repr = self._criar_representacoes(instancias, todas_pessoas)
        self.stdout.write(f'  {n_repr} representações')

        # 4. Projetos
        self.stdout.write('Criando projetos...')
        projetos = self._criar_projetos(pessoas_internas, instancias)
        self.stdout.write(f'  {len(projetos)} projetos')

        # 5. Missões + delegação
        self.stdout.write('Criando missões e delegações...')
        missoes, n_membros = self._criar_missoes(todas_pessoas, instancias)
        self.stdout.write(f'  {len(missoes)} missões com {n_membros} membros de delegação')

        # 6. Atividades das instâncias
        self.stdout.write('Criando atividades (reuniões) das instâncias...')
        n_atividades = self._criar_atividades(instancias)
        self.stdout.write(f'  {n_atividades} atividades')

        # 7. Eventos extras
        self.stdout.write('Criando eventos extras com participações...')
        n_eventos, n_participacoes = self._criar_eventos(instancias, todas_pessoas, municipios)
        self.stdout.write(f'  {n_eventos} eventos com {n_participacoes} participações')

        # 8. Documentos fictícios anexados a algumas entidades
        self.stdout.write('Criando documentos ficticios...')
        n_docs = self._criar_documentos()
        self.stdout.write(f'  {n_docs} documentos')

        self.stdout.write(self.style.SUCCESS('Concluído!'))

    def _criar_documentos(self):
        """Anexa 1-3 documentos a uma amostra de entidades de cada categoria."""
        tipos = list(Documento.TipoDocumento.values)
        nomes_tipo = {
            'pauta': ['Pauta da reuniao', 'Pauta consolidada', 'Pauta preliminar'],
            'ata': ['Ata da reuniao', 'Ata consolidada', 'Ata aprovada'],
            'apresentacao': ['Apresentacao FNP', 'Slides oficiais', 'Apresentacao tecnica'],
            'relatorio': ['Relatorio executivo', 'Relatorio anual', 'Relatorio tecnico'],
            'lista_presenca': ['Lista de presenca', 'Lista assinada'],
            'certificado': ['Certificado de participacao'],
            'oficio': ['Oficio de indicacao', 'Oficio circular'],
            'decreto_lei': ['Decreto regulamentador', 'Portaria de criacao'],
            'outro': ['Documento anexo'],
        }
        total = 0
        amostras = [
            ('instancias', 'instancia', Instancia.objects.all()[:10]),
            ('projetos', 'projeto', Projeto.objects.all()[:10]),
            ('missoes', 'missao', Missao.objects.all()[:10]),
            ('atividades', 'atividade', Atividade.objects.all()[:15]),
            ('eventos', 'evento', Evento.objects.all()[:10]),
        ]
        for app_label, model_name, queryset in amostras:
            content_type = ContentType.objects.get(app_label=app_label, model=model_name)
            for obj in queryset:
                n = random.randint(1, 3)
                for _ in range(n):
                    tipo = random.choice(tipos)
                    base = nomes_tipo.get(tipo, ['Documento'])
                    nome = f'{random.choice(base)} — {obj}'[:255]
                    _, criado = Documento.objects.get_or_create(
                        content_type=content_type,
                        object_id=obj.pk,
                        nome=nome,
                        defaults={
                            'tipo': tipo,
                            'link_externo': f'https://exemplo.fnp.org.br/docs/{random.randint(10000, 99999)}.pdf',
                            'descricao': 'Documento ficticio de demonstracao.',
                        },
                    )
                    if criado:
                        total += 1
        return total

    def _criar_pessoas_extras(self, municipios):
        """Cria pessoas adicionais, distribuindo aleatoriamente entre municípios."""
        criadas = 0
        for nome, tipo in PESSOAS_EXTRAS:
            email = nome.lower().replace(' ', '.') + '@exemplo.fnp.org.br'
            pessoa, criada = Pessoa.objects.get_or_create(
                email=email,
                defaults={
                    'nome': nome,
                    'tipo': tipo,
                    'genero': random.choice(GENEROS),
                    'cargo': self._cargo_para_tipo(tipo),
                    'partido': random.choice(PARTIDOS) if tipo != 'interno' else '',
                    'telefone': f'(11) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}',
                    'autorizacao_uso_imagem': random.choice([True, True, False]),
                    'termo_confidencialidade': random.choice([True, False]),
                    'ativo': True,
                },
            )
            if criada:
                criadas += 1
                if tipo != 'interno':
                    municipio = random.choice(municipios)
                    VinculoMunicipio.objects.get_or_create(
                        pessoa=pessoa,
                        municipio=municipio,
                        papel=self._papel_vinculo(tipo),
                        inicio_mandato=date(2025, 1, 1),
                        defaults={
                            'fim_mandato': date(2028, 12, 31),
                            'vigente': True,
                        },
                    )
        return criadas

    def _cargo_para_tipo(self, tipo):
        """Retorna um cargo plausível para o tipo de pessoa."""
        cargos = {
            'prefeito': 'Prefeito(a)',
            'vice_prefeito': 'Vice-prefeito(a)',
            'secretario': random.choice([
                'Secretário(a) de Saúde',
                'Secretário(a) de Educação',
                'Secretário(a) de Meio Ambiente',
                'Secretário(a) de Mobilidade',
                'Secretário(a) de Habitação',
            ]),
            'assessor': 'Assessor(a) Técnico(a)',
            'vereador': 'Vereador(a)',
            'interno': random.choice([
                'Coordenador(a) Técnico(a)',
                'Analista de Projetos',
                'Assessor(a) Institucional',
                'Gerente de Articulação',
            ]),
        }
        return cargos.get(tipo, 'Outro')

    def _papel_vinculo(self, tipo_pessoa):
        """Mapeia o tipo de pessoa para o papel correspondente no vínculo municipal."""
        mapa = {
            'prefeito': VinculoMunicipio.Papel.PREFEITO,
            'vice_prefeito': VinculoMunicipio.Papel.VICE_PREFEITO,
            'secretario': VinculoMunicipio.Papel.SECRETARIO,
            'assessor': VinculoMunicipio.Papel.ASSESSOR,
            'vereador': VinculoMunicipio.Papel.VEREADOR,
        }
        return mapa.get(tipo_pessoa, VinculoMunicipio.Papel.CONTATO)

    def _criar_instancias(self, pessoas_internas):
        """Cria instâncias com arcabouço legal e composição variadas."""
        instancias = []
        status_opts = [
            Instancia.Status.EM_FUNCIONAMENTO,
            Instancia.Status.EM_FUNCIONAMENTO,
            Instancia.Status.EM_CONSTRUCAO,
            Instancia.Status.INATIVO,
        ]
        tipos_arcabouco = list(Instancia.TipoArcabouco.values)
        tempos_mandato = list(Instancia.TempoMandato.values)
        periodicidades = list(Instancia.Periodicidade.values)

        for nome, origem, forma, categoria in INSTANCIAS_DADOS:
            instancia, _ = Instancia.objects.get_or_create(
                nome=nome,
                defaults={
                    'origem': origem,
                    'forma': forma,
                    'categoria': categoria,
                    'tipo_arcabouco': random.choice(tipos_arcabouco),
                    'numero_arcabouco': f'{random.choice(["Lei", "Decreto", "Portaria"])} {random.randint(100, 9999)}/{random.randint(2018, 2025)}',
                    'status': random.choice(status_opts),
                    'composicao': {
                        'federal': random.randint(1, 5),
                        'estadual': random.randint(1, 5),
                        'municipal': random.randint(3, 12),
                        'sociedade_civil': random.randint(0, 4),
                    },
                    'tempo_mandato': random.choice(tempos_mandato),
                    'periodicidade_reunioes': random.choice(periodicidades),
                    'possui_gt_ct': random.choice([True, False]),
                    'link_site': f'https://exemplo.fnp.org.br/instancia/{random.randint(100, 999)}',
                    'ponto_focal_fnp': random.choice(pessoas_internas) if pessoas_internas else None,
                    'descricao': f'Espaço institucional para articulação sobre {nome.lower()}.',
                },
            )
            instancias.append(instancia)
        return instancias

    def _criar_representacoes(self, instancias, pessoas):
        """Atribui aleatoriamente 3-8 representantes a cada instância."""
        funcoes = list(Representacao.Funcao.values)
        tipos_mandato = list(Representacao.TipoMandato.values)
        docs_indicacao = list(Representacao.DocumentoIndicacao.values)
        total = 0
        for instancia in instancias:
            n = random.randint(3, 8)
            amostra = random.sample(pessoas, min(n, len(pessoas)))
            for pessoa in amostra:
                inicio = date(random.randint(2023, 2025), random.randint(1, 12), 1)
                fim = inicio + timedelta(days=random.choice([365, 730, 1095]))
                _, criada = Representacao.objects.get_or_create(
                    instancia=instancia,
                    pessoa=pessoa,
                    funcao=random.choice(funcoes),
                    inicio_mandato=inicio,
                    defaults={
                        'tipo_mandato': random.choice(tipos_mandato),
                        'documento_indicacao': random.choice(docs_indicacao),
                        'fim_mandato': fim,
                        'autorizacao_uso_imagem': random.choice([True, False]),
                        'termo_confidencialidade': random.choice([True, False]),
                        'vigente': fim >= timezone.now().date(),
                    },
                )
                if criada:
                    total += 1
        return total

    def _criar_projetos(self, pessoas_internas, instancias):
        """Cria projetos com responsável interno e vínculo opcional a uma instância."""
        projetos = []
        status_opts = list(Projeto.Status.values)
        fontes = list(Projeto.FontesRecurso.values)
        for nome, descricao in PROJETOS_DADOS:
            inicio = date(2025, random.randint(1, 12), 1)
            projeto, _ = Projeto.objects.get_or_create(
                nome=nome,
                defaults={
                    'descricao': descricao,
                    'objetivo': f'Atingir resultados concretos em {descricao.lower()}',
                    'status': random.choice(status_opts),
                    'fonte_recurso': random.choice(fontes),
                    'valor_orcado': Decimal(random.randint(50_000, 5_000_000)),
                    'data_inicio': inicio,
                    'data_fim_previsto': inicio + timedelta(days=random.randint(180, 1095)),
                    'responsavel': random.choice(pessoas_internas) if pessoas_internas else None,
                    'instancia_vinculada': random.choice(instancias) if random.random() > 0.4 else None,
                },
            )
            projetos.append(projeto)
        return projetos

    def _criar_missoes(self, pessoas, instancias):
        """Cria missões com delegação de 3-7 pessoas e chefe destacado."""
        missoes = []
        total_membros = 0
        papeis = list(MembroDelegacao.Papel.values)
        for titulo, tipo, pais, cidade in MISSOES_DADOS:
            inicio = date(2025, random.randint(1, 12), random.randint(1, 28))
            chefe = random.choice(pessoas)
            missao, criada = Missao.objects.get_or_create(
                titulo=titulo,
                defaults={
                    'tipo': tipo,
                    'status': random.choice(list(Missao.Status.values)),
                    'pais': pais,
                    'cidade': cidade,
                    'objetivo': f'Articulação e intercâmbio técnico em {cidade}.',
                    'data_inicio': inicio,
                    'data_fim': inicio + timedelta(days=random.randint(3, 10)),
                    'chefe_delegacao': chefe,
                    'instancia_vinculada': random.choice(instancias) if random.random() > 0.5 else None,
                    'relatorio_resumo': '',
                },
            )
            missoes.append(missao)
            if criada:
                membros = random.sample(pessoas, min(random.randint(3, 7), len(pessoas)))
                for membro in membros:
                    papel = MembroDelegacao.Papel.CHEFE if membro == chefe else random.choice(papeis)
                    _, c = MembroDelegacao.objects.get_or_create(
                        missao=missao,
                        pessoa=membro,
                        defaults={'papel': papel},
                    )
                    if c:
                        total_membros += 1
        return missoes, total_membros

    def _criar_atividades(self, instancias):
        """Cria 1-3 atividades (reuniões) por instância em datas espalhadas no último ano."""
        formatos = list(Atividade.Formato.values)
        status_opts = list(Atividade.Status.values)
        total = 0
        for instancia in instancias:
            n = random.randint(1, 3)
            for _ in range(n):
                dias_atras = random.randint(0, 365)
                data = date.today() - timedelta(days=dias_atras)
                _, criada = Atividade.objects.get_or_create(
                    instancia=instancia,
                    data_reuniao=data,
                    defaults={
                        'formato': random.choice(formatos),
                        'tipo_calendario': random.choice(list(Atividade.TipoCalendario.values)),
                        'status': Atividade.Status.REALIZADA if dias_atras > 7 else random.choice(status_opts),
                        'local': f'Sala virtual {random.randint(100, 999)}',
                        'pauta_resumo': f'Discussão de pontos prioritários da agenda da {instancia.nome}.',
                        'ata_resumo': 'Deliberações registradas conforme regimento.' if dias_atras > 7 else '',
                        'possui_pauta': True,
                        'possui_ata': dias_atras > 7,
                        'possui_lista_presenca': dias_atras > 7,
                    },
                )
                if criada:
                    total += 1
        return total

    def _criar_eventos(self, instancias, pessoas, municipios):
        """Cria eventos extras com vínculo opcional a instância e 5-15 participações cada."""
        formas_part = list(Participacao.FormaParticipacao.values)
        papeis = list(Participacao.PapelNoEvento.values)
        modalidades = list(Evento.Modalidade.values)
        acessos = list(Evento.AcessoEvento.values)
        tipos_part_fnp = list(Evento.TipoParticipacaoFNP.values)
        total_eventos = 0
        total_participacoes = 0
        for titulo, tipo, objetivo, natureza in EVENTOS_DADOS:
            dias_atras = random.randint(-90, 365)
            data_inicio = date.today() - timedelta(days=dias_atras)
            evento, criado = Evento.objects.get_or_create(
                titulo=titulo,
                defaults={
                    'tipo': tipo,
                    'acesso': random.choice(acessos),
                    'tipo_participacao_fnp': random.choice(tipos_part_fnp),
                    'objetivo': objetivo,
                    'natureza': natureza,
                    'modalidade': random.choice(modalidades),
                    'instancia_vinculada': random.choice(instancias) if random.random() > 0.5 else None,
                    'data_inicio': data_inicio,
                    'data_fim': data_inicio + timedelta(days=random.randint(0, 3)),
                    'cidade': random.choice(['Brasília', 'São Paulo', 'Rio de Janeiro', 'Recife', 'Curitiba']),
                    'uf': random.choice(['DF', 'SP', 'RJ', 'PE', 'PR']),
                    'descricao': f'Evento institucional do tipo {tipo}.',
                },
            )
            if criado:
                total_eventos += 1
                amostra = random.sample(pessoas, min(random.randint(5, 15), len(pessoas)))
                for pessoa in amostra:
                    vinculo = pessoa.vinculos.filter(vigente=True).first()
                    municipio = vinculo.municipio if vinculo else random.choice(municipios)
                    _, c = Participacao.objects.get_or_create(
                        pessoa=pessoa,
                        evento=evento,
                        defaults={
                            'municipio': municipio,
                            'forma_participacao': random.choice(formas_part),
                            'papel_no_evento': random.choice(papeis),
                            'confirmado': random.choice([True, True, False]),
                        },
                    )
                    if c:
                        total_participacoes += 1
        return total_eventos, total_participacoes
