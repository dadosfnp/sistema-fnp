"""Management command que popula o Dicionário com os termos da máscara FNP.

Os termos vêm da aba "Dicionario" da planilha
``Máscara_Monitoramento_Representações - FNP.xlsx`` e são mantidos
aqui hard-coded para que o seed seja reprodutível sem dependência
externa em ambientes de demonstração.
"""

from django.core.management.base import BaseCommand

from aplicacoes.dicionario.models import TermoDicionario


TERMOS = [
    # Sobre as Instâncias
    ('instancias', 'Instância de representação',
     'Estrutura institucional de participação social ou representação.',
     'Conselhos, comitês, comissão, fórum, associação, rede', 10),
    ('instancias', 'Classificação das Instâncias de representação',
     'A classificação das instâncias de representação internas e externas, especialmente no contexto de governança, gestão e administração, refere-se aos diferentes órgãos, conselhos e grupos que atuam dentro ou fora de uma organização para monitorar, direcionar e representar interesses.',
     'Interna ou externa', 20),
    ('instancias', 'Instâncias de representação internas',
     'Instâncias de participação criadas pela FNP para debater determinados temas, podendo ser gerenciadas por secretários(as) e gestores(as) municipais (Fóruns) ou cuja governança é composta por Prefeitas e Prefeitos associados à FNP (Comissões Permanentes).',
     'Fórum ou Comissão', 30),
    ('instancias', 'Instâncias de representação externas',
     'Instância de participação responsável por tomar decisões coletivas dentro de uma determinada política ou temática, cujas representações da FNP são designadas por meio de documento oficial (conselhos, comissões, comitês) ou cuja participação e representação da FNP ocorrem de forma observativa (redes e associações).',
     'Conselhos, comissões, comitês, associações, redes', 40),
    ('instancias', 'Categoria',
     'Refere-se ao tipo de hierarquia na instância, sendo principal (a própria instância) ou secundária (GT, CT, subcomissão, etc.).',
     'Principal ou secundária', 50),
    ('instancias', 'Arcabouço Legal',
     'Conjunto de normas que fundamentam a existência e funcionamento da instância.',
     'Leis, decretos, portarias, DOU, resoluções etc.', 60),
    ('instancias', 'Decretos',
     'Normas complementares emitidas pelo poder executivo para regulamentar leis.',
     'Ex.: Decreto nº 7.890/2021', 70),
    ('instancias', 'Lei',
     'Norma jurídica aprovada pelo poder legislativo que institui ou regula a instância.',
     'Ex.: Lei nº 3434/2020', 80),
    ('instancias', 'Portarias',
     'Atos administrativos que formalizam designações e nomeações.',
     'Ex.: Portaria nº 45/2024', 90),
    ('instancias', 'Regimento Interno / Estatuto',
     'Documento que define regras de funcionamento, composição e competências da instância.',
     'Em elaboração, vigente ou desatualizado', 100),
    ('instancias', 'Status da Instância',
     'Situação atual de funcionamento ou desenvolvimento da instância.',
     'Em criação, em atualização, em andamento, inativo', 110),
    ('instancias', 'Composição',
     'Perfil qualitativo e quantitativo dos(as) representantes em uma determinada instância.',
     'Titulares/suplentes e esferas de representação', 120),
    ('instancias', 'Mandato',
     'Período durante o qual o representante exerce oficialmente a função. Pode variar conforme a instância.',
     'Varia conforme a instância', 130),
    ('instancias', 'Tempo do Mandato',
     'Duração prevista do mandato do representante.',
     '1 ano, 2 anos, 3 anos, 4 anos', 140),
    ('instancias', 'Periodicidade das Reuniões',
     'Define de quanto em quanto tempo a instância se reúne para monitorar e tomar decisões.',
     'Mensal, bimestral, semestral, trimestral, semanal, em definição', 150),
    ('instancias', 'Existência de GT e CT',
     'São espaços de aprofundamento técnico para analisar cada detalhe de uma pauta complexa.',
     'Sim ou não', 160),
    ('instancias', 'Link',
     'Hiperlink: elemento interativo (texto, imagem ou botão) que ao ser clicado direciona o usuário para outro local, documento ou site.',
     '', 170),
    ('instancias', 'Ponto Focal — FNP',
     'Profissional técnico vinculado à FNP que atua em atividades de apoio ou representação, sem exercer função oficialmente designada.',
     'Ex.: equipe técnica de articulação', 180),

    # Sobre os Representantes
    ('representantes', 'Identificação do(a) representante',
     'Informações sobre nome, contatos (celular e e-mail) e município/UF.',
     '', 10),
    ('representantes', 'Cargo',
     'Posição formal que uma pessoa ocupa dentro da estrutura de uma organização (pública ou privada), definindo seu título, hierarquia e responsabilidades.',
     'Presidente, Secretário, Diretor, Assessor, Técnico, etc.', 20),
    ('representantes', 'Gênero',
     'Identificação de gênero autodeclarada do representante.',
     'Feminino, Masculino, Outro, Prefere não declarar', 30),
    ('representantes', 'Representações',
     'Pessoas designadas oficialmente para representar a instituição em determinada instância.',
     'Titulares e Suplentes', 40),
    ('representantes', 'Titular',
     'Representante principal indicado para participar das reuniões e decisões. Tem direito a voto e fala conforme o regimento.',
     '', 50),
    ('representantes', 'Suplente',
     'Representante substituto que assume na ausência do titular. Deve acompanhar as atividades da instância.',
     '', 60),
    ('representantes', 'Função na Instância',
     'Cargo ou função ocupada pelo representante na instituição que o indica.',
     'Presidente, Secretário, Membro, Coordenador, Técnico, Diretor', 70),
    ('representantes', 'Documento de indicação',
     'Documento oficial que formaliza a indicação ou nomeação do representante.',
     'Publicação em DOU, Ofício, Portaria, E-mail, Ata', 80),
    ('representantes', 'Tipo de mandato',
     'Identifica se a pessoa está em seu primeiro mandato, segundo ou foi reconduzida ao cargo.',
     '1º Mandato, 2º Mandato, Recondução', 90),
    ('representantes', 'Autorização de uso de imagem',
     'Termo assinado pelo representante autorizando o uso de sua imagem em comunicações da FNP.',
     'Sim / Não', 100),
    ('representantes', 'Termo de confidencialidade',
     'Termo assinado pelo representante para tratamento sigiloso de informações sensíveis quando aplicável à função.',
     'Sim / Não', 110),

    # Sobre as Atividades
    ('atividades', 'Atividade',
     'Reunião, encontro ou agenda específica de uma instância. Cada atividade tem data, formato e indica se há pauta, ata e lista de presença registradas.',
     '', 10),
    ('atividades', 'Formato das reuniões',
     'Como a reunião é realizada — presencialmente, online ou de modo híbrido.',
     'Presencial, Virtual, Híbrida', 20),
    ('atividades', 'Calendário das reuniões',
     'Classificação da reunião quanto à previsibilidade no calendário da instância.',
     'Ordinária, Extraordinária', 30),
    ('atividades', 'Pauta',
     'Lista de assuntos a serem tratados na reunião.',
     'Documento anexável', 40),
    ('atividades', 'Ata',
     'Registro formal das discussões e deliberações de uma reunião.',
     'Documento anexável', 50),
    ('atividades', 'Lista de Presença',
     'Documento que registra os participantes que estiveram presentes na reunião.',
     'Documento anexável', 60),

    # Sobre os Eventos
    ('eventos', 'Tipo de Evento',
     'Categoria conceitual do evento (assembleia, audiência, congresso, etc.).',
     'Assembleia Geral, Audiência, Comissões, Conferência, Congresso, Grupos de Trabalho, Missão Internacional, Reunião de Projeto, Seminário, Workshop', 10),
    ('eventos', 'Acesso ao Evento',
     'Regra de entrada do evento — quem pode participar e em que condições.',
     'Público, Privado, Restrito, Gratuito, Inscrição paga', 20),
    ('eventos', 'Tipo de Participação',
     'Papel institucional da FNP no evento.',
     'Apoio Institucional, Realização, Co-realização, Patrocinador, Técnico, Político-institucional', 30),
    ('eventos', 'Função no Evento',
     'Papel exercido pela pessoa durante o evento.',
     'Coordenação, Expositor, Observador, Palestrante, Participante', 40),
    ('eventos', 'Objetivo do Evento',
     'Resultado pretendido com a realização do evento.',
     'Articulação política, Formação/Capacitação, Incidência institucional, Tomada de decisão', 50),
    ('eventos', 'Formato do Evento',
     'Como o evento é realizado.',
     'Presencial, Virtual, Híbrida', 60),
    ('eventos', 'Vínculo com Espaço de Diálogo',
     'Indica se o evento está relacionado a alguma instância (espaço de diálogo federativo) já cadastrada.',
     'Sim (e qual) / Não', 70),
    ('eventos', 'Natureza do Evento',
     'Caráter decisório ou formativo do evento.',
     'Deliberativo, Consultivo, Formativo', 80),

    # Sobre os Projetos
    ('projetos', 'Projeto',
     'Iniciativa institucional com escopo, prazo e responsáveis definidos. Tem começo, meio e fim, diferente de uma instância (permanente) ou evento (pontual).',
     '', 10),
    ('projetos', 'Fonte de Recurso',
     'Origem do financiamento do projeto.',
     'Recurso próprio, Parceria, Convênio, Emenda parlamentar, Cooperação internacional', 20),
    ('projetos', 'Status do Projeto',
     'Situação atual de execução do projeto.',
     'Em planejamento, Em andamento, Pausado, Concluído, Cancelado', 30),

    # Sobre as Missões
    ('missoes', 'Missão',
     'Deslocamento institucional da FNP, nacional ou internacional, com objetivo específico (encontros, viagens, intercâmbios técnicos).',
     '', 10),
    ('missoes', 'Delegação',
     'Conjunto de pessoas que integram a missão, com chefe formalmente designado e demais membros em papéis técnicos ou representativos.',
     '', 20),
    ('missoes', 'Chefe da Delegação',
     'Pessoa designada formalmente para liderar a delegação da missão.',
     '', 30),

    # Gerais
    ('geral', 'Adimplência',
     'Situação do município quanto ao pagamento da contribuição anual à FNP.',
     'Adimplente / Inadimplente', 10),
    ('geral', 'Engajamento',
     'Pontuação consolidada que mede a participação ativa de um município nas atividades, eventos, instâncias e missões da FNP.',
     'Pontuação numérica e nível (alto/médio/baixo)', 20),
    ('geral', 'Município associado',
     'Município que possui vínculo formal de associação à FNP e contribui regularmente.',
     'Sim / Não', 30),
    ('geral', 'Pauta temática',
     'Eixo de atuação institucional (ex.: saúde, mobilidade, segurança) que organiza projetos, eventos e instâncias.',
     '', 40),
]


class Command(BaseCommand):
    """Popula o dicionário institucional com os termos da máscara FNP."""

    help = 'Cria/atualiza os termos do dicionário institucional.'

    def handle(self, *args, **options):
        criados = 0
        atualizados = 0
        for secao, termo, definicao, tipo_dado, ordem in TERMOS:
            obj, criado = TermoDicionario.objects.update_or_create(
                termo=termo,
                defaults={
                    'secao': secao,
                    'definicao': definicao,
                    'tipo_de_dado': tipo_dado,
                    'ordem': ordem,
                    'ativo': True,
                },
            )
            if criado:
                criados += 1
            else:
                atualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Concluido: {criados} criados, {atualizados} atualizados, {len(TERMOS)} total.'
        ))
