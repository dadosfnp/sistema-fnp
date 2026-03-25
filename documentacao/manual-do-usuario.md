# Manual do Usuario — Sistema FNP

## O que e o Sistema FNP?

O Sistema FNP e a plataforma de gestao institucional da **Frente Nacional de Prefeitos**. Ele centraliza o cadastro de pessoas (prefeitos, secretarios, equipe interna), municipios, controle de adimplencia, eventos e engajamento — tudo que antes ficava espalhado em planilhas.

---

## Acesso ao Sistema

### Como entrar

1. Abra o navegador e acesse o endereco do sistema
2. Na tela de login, informe seu **usuario** e **senha**
3. Clique em **Entrar**

> Se nao tem acesso, solicite ao administrador de TI.

### Perfis de acesso

| Perfil | O que pode fazer |
|--------|-----------------|
| **Visualizador** | Consultar todas as informacoes: pessoas, municipios, adimplencia, eventos, engajamento |
| **Editor** | Tudo do visualizador + cadastrar novas pessoas/municipios e editar registros existentes |
| **Administrador** | Gestao de usuarios, permissoes e logs de auditoria (acesso via painel Admin) |

### Como sair

Clique em **Sair** no canto superior direito da tela.

---

## Navegacao

O sistema possui um **menu lateral** (sidebar) com as seguintes secoes:

- **Inicio** — Painel geral com indicadores e atalhos rapidos
- **Pessoas** — Cadastro de prefeitos, secretarios, assessores e equipe interna
- **Municipios** — Cadastro de municipios brasileiros
- **Adimplencia** — Controle de pagamentos anuais dos municipios
- **Eventos** — Reunioes, foruns, congressos e webinars da FNP
- **Engajamento** — Ranking de participacao dos municipios
- **Relatorios** — Dashboards e exportacoes (em desenvolvimento)

O menu pode ser **recolhido** clicando no botao "Recolher" na parte inferior, deixando apenas os icones visiveis.

---

## Pagina Inicial (Dashboard)

Ao entrar, voce vera o **Painel Geral** com:

- **Indicadores** no topo: total de pessoas, municipios (e quantos sao associados), eventos e situacao de adimplencia do ano
- **Eventos Recentes**: lista dos ultimos 5 eventos cadastrados — clique para ver detalhes
- **Top Engajamento**: ranking dos 5 municipios mais engajados com barra de progresso
- **Atalhos rapidos**: acesso direto a cada secao do sistema

---

## Pessoas

### Consultar pessoas

1. No menu lateral, clique em **Pessoas**
2. A lista mostra: nome, tipo (prefeito, secretario, etc.), partido, cargo e status
3. Use o campo **"Pesquisar pessoas..."** para filtrar por nome, cargo ou partido — a busca e em tempo real

### Ver detalhes de uma pessoa

Clique em qualquer linha da lista para abrir a pagina de detalhe, que mostra:

- **Dados pessoais**: cargo, genero, periodo do mandato
- **Vinculos com municipios**: quais municipios a pessoa representa e em qual papel
- **Participacoes em eventos**: historico de eventos com forma de participacao e pontos

### Cadastrar nova pessoa (somente Editor)

1. Na lista de pessoas, clique no botao **"+ Nova Pessoa"** (canto superior direito)
2. Preencha os campos do formulario
3. Clique em **Cadastrar**

### Editar pessoa (somente Editor)

1. Abra o detalhe da pessoa
2. Clique no botao **"Editar"** ao lado do nome
3. Altere os campos desejados
4. Clique em **Salvar**

> Toda edicao fica registrada no log de auditoria com o nome de quem alterou.

---

## Municipios

### Consultar municipios

1. No menu lateral, clique em **Municipios**
2. A lista mostra: nome, UF, regiao, populacao e se e associado FNP
3. Use o campo de busca para filtrar por nome ou UF

### Ver detalhes de um municipio

Clique em qualquer municipio para ver:

- **Mapa**: localizacao geografica do municipio (se houver coordenadas cadastradas)
- **Informacoes**: populacao, codigo IBGE, se e capital, score de engajamento
- **Representantes**: pessoas vinculadas ao municipio (prefeitos, secretarios)
- **Historico de adimplencia**: status de pagamento por ano
- **Participacoes em eventos**: historico de presenca do municipio

### Cadastrar / Editar municipio (somente Editor)

Mesma logica das pessoas: botao **"+ Novo Municipio"** na lista ou **"Editar"** no detalhe.

---

## Adimplencia

### O que e

A adimplencia controla se os municipios associados estao em dia com as contribuicoes anuais a FNP.

### Como consultar

1. No menu lateral, clique em **Adimplencia**
2. A tabela mostra: municipio, ano, status, valor devido, valor pago e data de pagamento
3. Use a busca para filtrar por municipio, UF ou status

### Status possiveis

| Status | Significado | Cor |
|--------|------------|-----|
| **Adimplente** | Pagamento em dia | Verde |
| **Inadimplente** | Sem pagamento | Vermelho |
| **Parcial** | Pagamento parcial | Amarelo |

> O status de adimplencia impacta diretamente a pontuacao de engajamento do municipio (inadimplentes recebem penalidade).

---

## Eventos

### Consultar eventos

1. No menu lateral, clique em **Eventos**
2. A lista mostra: titulo, tipo, modalidade, data e local
3. Busque por titulo, local ou tipo

### Ver detalhes de um evento

Clique no evento para ver:

- **Informacoes gerais**: tipo, modalidade (presencial/online/hibrido), datas, local
- **Pontuacao**: quantos pontos o evento vale (presencial, online, bonus palestrante/organizador)
- **Participantes confirmados**: lista com nome, municipio, forma de participacao, papel e pontos

### Tipos de evento

- Reuniao Geral da FNP
- Forum
- Congresso
- Viagem internacional/nacional
- Reuniao presencial/online
- Webinar
- Presenca na FNP

---

## Engajamento

### O que e

O engajamento mede o nivel de participacao de cada municipio nos eventos da FNP durante o bienio (ex: 2025-2026).

### Como funciona a pontuacao

1. Cada **evento** tem uma pontuacao definida (ex: presencial = 10 pts, online = 5 pts)
2. A **meta** e calculada automaticamente: soma dos pontos presenciais de todos os eventos cadastrados no bienio
3. A **pontuacao normalizada** (0 a 100) e a proporcao entre pontos obtidos e meta
4. **Penalidades** de adimplencia reduzem a pontuacao (inadimplente perde 30%, parcial perde 15%)

### Niveis

| Nivel | Score | Significado |
|-------|-------|-------------|
| **Alto** | 70-100 | Municipio muito ativo |
| **Medio** | 40-69 | Participacao moderada |
| **Baixo** | 10-39 | Pouca participacao |
| **Inativo** | 0-9 | Sem participacao relevante |

### Como consultar

1. No menu lateral, clique em **Engajamento**
2. O ranking mostra: posicao, municipio, bienio, score (com barra visual), pontos brutos, participacoes e nivel
3. Clique em qualquer municipio para ver o detalhe completo

---

## Dicas Uteis

- **Busca em tempo real**: todas as paginas de listagem possuem campo de busca que filtra enquanto voce digita
- **Tudo e clicavel**: clique em qualquer item da lista para ver os detalhes completos
- **Navegacao por breadcrumb**: no topo de cada pagina de detalhe, voce pode clicar para voltar a lista
- **Menu recolhido**: recolha o menu lateral para ter mais espaco de tela — os icones continuam acessiveis

---

## Para o Administrador de TI

### Acesso ao painel Admin

1. Faca login com um usuario superusuario
2. Clique em **Admin** no canto superior direito (ou acesse `/admin/`)
3. No painel Admin voce pode:
   - **Gerenciar usuarios**: criar, editar, ativar/desativar contas
   - **Definir perfis**: atribuir perfil de Editor ou Visualizador a cada usuario
   - **Consultar logs**: ver o historico de quem alterou o que e quando
   - **Gerenciar todos os dados**: pessoas, municipios, adimplencia, eventos, engajamento

### Criando um novo usuario

1. No Admin, va em **Usuarios > Adicionar usuario**
2. Defina username e senha
3. Na secao **Perfil de acesso**, selecione: Visualizador ou Editor
4. Salve

### Consultando logs de auditoria

1. No Admin, va em **Nucleo > Logs de alteracao**
2. Filtre por data, tipo de acao (criacao/edicao/exclusao) ou modelo
3. Cada log mostra: quem fez, o que fez, quando, e os campos que mudaram (antes/depois)

---

## Usuarios de Teste (Ambiente de Desenvolvimento)

| Usuario | Senha | Perfil |
|---------|-------|--------|
| `admin` | `admin123` | Superusuario (Admin TI) |
| `editor` | `editor123` | Editor |
| `visualizador` | `viewer123` | Visualizador |

> **Importante**: troque estas senhas antes de colocar em producao!
