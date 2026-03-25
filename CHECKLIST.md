# Sistema FNP — Checklist de Implementação

## Fase 0 — Antes da Apresentação

| # | Tarefa | Prazo | Status |
|---|--------|-------|--------|
| 1 | Criar repositório privado no GitHub: sistema-fnp | Esta semana | FEITO |
| 2 | Commitar a pasta documentacao/ com diagramas Mermaid e RDAs | Esta semana | FEITO |
| 3 | Revisar o deck de apresentação e adaptar ao tom da diretoria | Esta semana | |
| 4 | Apresentar para a equipe — obter aprovação para iniciar | Esta semana | |

## Fase 1 — Fundação

| # | Tarefa | Prazo | Status |
|---|--------|-------|--------|
| 5 | Instalar Python 3.12, Django 5.x, PostgreSQL local | Semanas 1-2 | PARCIAL (falta PostgreSQL) |
| 6 | Criar projeto Django com a estrutura de apps definida | Semanas 1-2 | FEITO |
| 7 | Implementar models: Pessoa, Município, VínculoMunicípio, Pauta | Semanas 1-2 | FEITO |
| 8 | Configurar Django Admin com django-unfold | Semanas 1-2 | FEITO |
| 9 | Escrever comando de importação das planilhas Google Sheets | Semanas 1-2 | |
| 10 | Importar dados das planilhas e validar integridade | Semanas 1-2 | |
| 11 | Primeiro deploy em homologação (Railway ou Render) | Semanas 1-2 | |

## Fase 2 — Interface de Cadastro

| # | Tarefa | Prazo | Status |
|---|--------|-------|--------|
| 12 | Instalar HTMX + Tailwind CSS + Alpine.js | Semanas 3-4 | FEITO |
| 13 | Criar template base com sidebar e navegação | Semanas 3-4 | FEITO |
| 14 | Tela de listagem de pessoas (com busca dinâmica HTMX) | Semanas 3-4 | |
| 15 | Tela de detalhe de pessoa (vínculos, histórico) | Semanas 3-4 | |
| 16 | Tela de listagem e detalhe de municípios | Semanas 3-4 | |
| 17 | Formulários de criação/edição com validação | Semanas 3-4 | |

## Fase 3 — Adimplência

| # | Tarefa | Prazo | Status |
|---|--------|-------|--------|
| 18 | Implementar models de Adimplência + Admin | Semanas 5-6 | FEITO |
| 19 | Tela de status por município (adimplente/inadimplente) | Semanas 5-6 | |
| 20 | Histórico de pagamentos e alertas | Semanas 5-6 | |
| 21 | Filtros: por UF, por status, por ano | Semanas 5-6 | |

## Fase 4 — Engajamento + Eventos

| # | Tarefa | Prazo | Status |
|---|--------|-------|--------|
| 22 | Implementar models de Evento, Participação e Engajamento | Semanas 7-8 | FEITO |
| 23 | Signal que recalcula pontuação ao registrar participação | Semanas 7-8 | FEITO |
| 24 | Tela de eventos + registro de participação | Semanas 7-8 | |
| 25 | Ranking de engajamento por município (com status adimplência) | Semanas 7-8 | |

## Fase 5 — Relatórios e Dashboards

| # | Tarefa | Prazo | Status |
|---|--------|-------|--------|
| 26 | Dashboard principal com indicadores-chave | Semanas 9-10 | |
| 27 | Gráficos com Chart.js (adimplência, engajamento por região) | Semanas 9-10 | |
| 28 | Exportação PDF e Excel de relatórios | Semanas 9-10 | |

## Fase 6 — Produção

| # | Tarefa | Prazo | Status |
|---|--------|-------|--------|
| 29 | Testes automatizados (pytest + factory_boy) | Semanas 11-12 | |
| 30 | CI/CD com GitHub Actions (testes automáticos a cada push) | Semanas 11-12 | |
| 31 | Migração final dos dados das planilhas | Semanas 11-12 | |
| 32 | Deploy em produção | Semanas 11-12 | |
| 33 | Treinamento da equipe + documentação de uso | Semanas 11-12 | |
| 34 | Desativar planilhas Google Sheets como fonte de dados | Semanas 11-12 | |
