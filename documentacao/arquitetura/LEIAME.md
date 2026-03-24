# Sistema FNP — Documentação de Arquitetura

> **Versão:** 1.0.0  
> **Data:** 2026-03-24  
> **Autor:** Equipe de Tecnologia — FNP  
> **Status:** Em construção

---

## 1. Visão geral

O Sistema FNP é a plataforma unificada de gestão institucional da Frente Nacional de Prefeitos. Centraliza o cadastro de pessoas (equipe interna, prefeitos, secretários, assessores), municípios associados, controle de adimplência, acompanhamento de engajamento e gestão de eventos.

### Objetivos

- Substituir planilhas Google Sheets por um sistema web integrado
- Centralizar dados de pessoas, municípios e relacionamentos em um único lugar
- Controlar adimplência dos municípios associados
- Medir e acompanhar o engajamento institucional
- Registrar participações em fóruns, reuniões e eventos
- Oferecer dashboards e relatórios para tomada de decisão

### Convenção de nomenclatura

| Escopo | Idioma | Exemplos |
|--------|--------|----------|
| Apps, models, campos, URLs, templates, pastas, commits, branches | **PT-BR** | `cadastro/`, `Pessoa`, `nome`, `lista_pessoas.html` |
| Arquivos técnicos do Django | **Inglês (padrão do framework)** | `models.py`, `views.py`, `urls.py`, `admin.py`, `manage.py` |

---

## 2. Diagrama de contexto (C4 — Nível 1)

Visão de alto nível: quem usa o sistema e com o que ele se integra.

```mermaid
C4Context
    title Sistema FNP — Diagrama de contexto

    Person(interno, "Equipe interna FNP", "Gestores, analistas e coordenadores")
    Person(gestor, "Gestores municipais", "Prefeitos e secretários consultam dados")

    System(fnp, "Sistema FNP", "Plataforma web de gestão institucional")

    System_Ext(planilhas, "Google Sheets", "Fonte de dados legada (migração)")
    System_Ext(email, "Serviço de e-mail", "Notificações e comunicação")
    System_Ext(ibge, "API IBGE", "Dados de municípios e população")

    Rel(interno, fnp, "Cadastra, consulta, gera relatórios")
    Rel(gestor, fnp, "Consulta dados do município")
    Rel(fnp, planilhas, "Importa dados iniciais")
    Rel(fnp, email, "Envia notificações")
    Rel(fnp, ibge, "Consulta dados municipais")
```

---

## 3. Diagrama de containers (C4 — Nível 2)

Componentes técnicos do sistema e como se comunicam.

```mermaid
C4Container
    title Sistema FNP — Containers

    Person(usuario, "Usuário FNP")

    Container_Boundary(web, "Aplicação web") {
        Container(frontend, "Frontend", "Django Templates + HTMX + Tailwind", "Interface web responsiva e interativa")
        Container(backend, "Backend", "Django 5.x + Python 3.12", "Lógica de negócio, autenticação, API")
        Container(admin, "Admin", "Django Admin + Unfold", "Painel administrativo customizado")
    }

    ContainerDb(bd, "Banco de dados", "PostgreSQL 16", "Dados de pessoas, municípios, adimplência, engajamento")

    Rel(usuario, frontend, "Acessa via navegador", "HTTPS")
    Rel(usuario, admin, "Gerencia dados", "HTTPS")
    Rel(frontend, backend, "Requisições", "HTTP/HTMX")
    Rel(admin, backend, "Requisições", "HTTP")
    Rel(backend, bd, "Lê/escreve", "Django ORM")
```

---

## 4. Modelo de domínio (ERD)

Entidades principais e seus relacionamentos.

```mermaid
erDiagram
    PESSOA ||--o{ VINCULO_MUNICIPIO : "vinculada a"
    MUNICIPIO ||--o{ VINCULO_MUNICIPIO : "possui"
    MUNICIPIO ||--o{ ADIMPLENCIA : "registra"
    MUNICIPIO ||--o{ ENGAJAMENTO : "tem score"
    EVENTO ||--o{ PARTICIPACAO : "gera"
    PESSOA ||--o{ PARTICIPACAO : "participa"
    PARTICIPACAO }o--|| EVENTO : "referente a"

    PESSOA {
        uuid id PK
        string nome
        string email
        string telefone
        enum tipo "interno | prefeito | secretario | assessor | outro"
        string cargo
        string partido
        boolean ativo
        datetime criado_em
        datetime atualizado_em
    }

    MUNICIPIO {
        uuid id PK
        string nome
        string uf
        integer codigo_ibge
        integer populacao
        string regiao
        boolean eh_capital
        boolean associado_fnp
        datetime criado_em
    }

    VINCULO_MUNICIPIO {
        uuid id PK
        uuid pessoa_id FK
        uuid municipio_id FK
        enum papel "prefeito | secretario | assessor | contato"
        date inicio_mandato
        date fim_mandato
        boolean vigente
        text observacao
    }

    ADIMPLENCIA {
        uuid id PK
        uuid municipio_id FK
        integer ano_referencia
        enum status "adimplente | inadimplente | parcial"
        decimal valor_devido
        decimal valor_pago
        date data_pagamento
        text observacao
    }

    ENGAJAMENTO {
        uuid id PK
        uuid municipio_id FK
        integer pontuacao_total
        integer total_participacoes
        datetime ultima_interacao
        enum nivel "alto | medio | baixo | inativo"
    }

    EVENTO {
        uuid id PK
        string titulo
        enum tipo "forum | reuniao | evento_presencial | webinar"
        date data_inicio
        date data_fim
        string local
        text descricao
        integer peso_engajamento
    }

    PARTICIPACAO {
        uuid id PK
        uuid pessoa_id FK
        uuid evento_id FK
        enum tipo_participacao "presencial | virtual | palestrante | organizador"
        boolean confirmado
        datetime data_confirmacao
    }
```

---

## 5. Arquitetura de módulos (Django apps)

Cada módulo é um Django app independente com responsabilidades bem definidas.

```mermaid
graph TD
    subgraph "Camada de apresentação"
        FE["Frontend<br/>Django Templates + HTMX"]
        ADM["Admin<br/>Django Unfold"]
    end

    subgraph "Camada de aplicação"
        AUTH["nucleo<br/>Autenticação + RBAC"]
        CAD["cadastro<br/>Pessoa, Município, Vínculo"]
        ADIM["adimplencia<br/>Pagamentos, Status"]
        ENG["engajamento<br/>Pontuação, Histórico"]
        EVT["eventos<br/>Fóruns, Reuniões"]
        REL["relatorios<br/>Dashboards, Exportações"]
    end

    subgraph "Camada de infraestrutura"
        ORM["Django ORM"]
    end

    subgraph "Banco de dados"
        PG[(PostgreSQL)]
    end

    FE --> AUTH
    ADM --> AUTH
    AUTH --> CAD
    AUTH --> ADIM
    AUTH --> ENG
    AUTH --> EVT
    AUTH --> REL

    CAD --> ORM
    ADIM --> ORM
    ENG --> ORM
    EVT --> ORM
    REL --> ORM

    ADIM -.->|sinal| ENG
    EVT -.->|sinal| ENG

    ORM --> PG
```

---

## 6. Fluxo de engajamento

Como a pontuação de engajamento de um município é calculada e atualizada.

```mermaid
flowchart TD
    A[Evento é criado] --> B[Participações são registradas]
    B --> C{Pessoa tem vínculo<br/>com município?}
    C -->|Sim| D[Identifica município vinculado]
    C -->|Não| E[Registra participação avulsa]
    D --> F[Calcula pontos do evento]
    F --> G[Atualiza pontuação do município]
    G --> H{Pontuação > limite?}
    H -->|Alto >= 80| I["Nível: ALTO"]
    H -->|Médio 40-79| J["Nível: MÉDIO"]
    H -->|Baixo 10-39| K["Nível: BAIXO"]
    H -->|Inativo < 10| L["Nível: INATIVO"]

    M[Adimplência muda] -.->|Bônus/Penalidade| G
```

---

## 7. Stack tecnológica

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| **Linguagem** | Python 3.12 | Conhecimento existente na equipe, ecossistema maduro |
| **Framework** | Django 5.x | Batteries-included, ORM poderoso, Admin, segurança |
| **Banco de dados** | PostgreSQL 16 | Robustez, escalabilidade, extensões (busca textual) |
| **Frontend** | Django Templates + HTMX + Tailwind CSS + Alpine.js | Interatividade sem complexidade de SPA |
| **Admin** | Django Unfold | Visual moderno para o Django Admin |
| **Deploy** | Ambiente local + GitHub | Cada dev clona, cria venv e roda |
| **CI/CD** | GitHub Actions | Testes, lint, deploy automático |
| **Diagramas** | Mermaid.js | Versionáveis no Git, renderizam no GitHub |

---

## 8. Decisões de arquitetura (RDAs)

As decisões arquiteturais são documentadas em arquivos separados na pasta `decisoes/`:

- [RDA-001: Usar Django ao invés de Next.js](decisoes/001-usar-django.md)
- [RDA-002: PostgreSQL ao invés de Google Sheets](decisoes/002-postgres-ao-inves-de-planilhas.md)
- [RDA-003: HTMX ao invés de React/SPA](decisoes/003-htmx-ao-inves-de-react.md)
- [RDA-004: Mermaid.js para diagramas versionáveis](decisoes/004-mermaid-para-diagramas.md)

---

## 9. Roteiro de implementação

| Fase | Prazo | Escopo |
|------|-------|--------|
| **Fase 1 — Fundação** | Semanas 1-2 | Setup projeto, models base, Django Admin, migração planilhas |
| **Fase 2 — Cadastro** | Semanas 3-4 | Interface de cadastro (pessoa, município, vínculo), busca, filtros |
| **Fase 3 — Adimplência** | Semanas 5-6 | Registro de pagamentos, status, histórico, alertas |
| **Fase 4 — Engajamento** | Semanas 7-8 | Pontuação automática, eventos, participações, dashboard |
| **Fase 5 — Relatórios** | Semanas 9-10 | Dashboards, exportações PDF/Excel, visão gerencial |
| **Fase 6 — Refinamento** | Semanas 11-12 | Testes, performance, feedback da equipe, deploy produção |

---

## 10. Estrutura do repositório

```
sistema-fnp/
├── documentacao/
│   └── arquitetura/
│       ├── LEIAME.md                      # Este arquivo
│       └── decisoes/                      # RDAs
├── configuracao/                          # Settings do Django
│   ├── __init__.py
│   ├── base.py
│   ├── local.py
│   └── producao.py
├── aplicacoes/
│   ├── nucleo/                            # Mixins, modelo base, autenticação
│   ├── cadastro/                          # Pessoa, Município, Vínculo
│   ├── adimplencia/                       # Pagamentos, status
│   ├── engajamento/                       # Pontuação, histórico
│   ├── eventos/                           # Fóruns, reuniões
│   └── relatorios/                        # Dashboards, exportações
├── templates/
│   ├── base.html
│   └── componentes/                       # Componentes HTMX reutilizáveis
├── estaticos/
│   ├── css/
│   └── js/
├── requisitos/
│   ├── base.txt
│   ├── local.txt
│   └── producao.txt
├── .env.exemplo                           # Variáveis de ambiente (modelo)
├── .gitignore
├── manage.py
└── LEIAME.md
```
