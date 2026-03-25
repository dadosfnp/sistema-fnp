# Sistema FNP — Documentacao Tecnica

> Referencia completa para desenvolvedores. Descreve arquitetura, modelos de
> dados, fluxos de negocio, convencoes e decisoes de projeto.

## Sumario

1. [Visao Geral](#visao-geral)
2. [Stack e Dependencias](#stack-e-dependencias)
3. [Estrutura de Diretorios](#estrutura-de-diretorios)
4. [Configuracao (Settings)](#configuracao-settings)
5. [Aplicacoes](#aplicacoes)
   - [nucleo](#nucleo)
   - [cadastro](#cadastro)
   - [adimplencia](#adimplencia)
   - [engajamento](#engajamento)
   - [eventos](#eventos)
   - [relatorios](#relatorios)
6. [Modelo de Dados](#modelo-de-dados)
7. [Autenticacao e Permissoes](#autenticacao-e-permissoes)
8. [Auditoria](#auditoria)
9. [Motor de Engajamento](#motor-de-engajamento)
10. [Frontend e Templates](#frontend-e-templates)
11. [Rotas (URLs)](#rotas-urls)
12. [Comandos de Gestao](#comandos-de-gestao)
13. [Convencoes de Codigo](#convencoes-de-codigo)
14. [Decisoes de Projeto (ADRs)](#decisoes-de-projeto-adrs)

---

## Visao Geral

Plataforma web de gestao institucional da **Frente Nacional de Prefeitos**.
Substitui planilhas Google Sheets por um sistema web com controle de acesso,
auditoria e calculo automatico de engajamento.

**Dominios principais:**

```
Pessoa ──┬── VinculoMunicipio ──── Municipio
         │                            │
         └── Participacao ──┐    Adimplencia
                            │         │
                        Evento   Engajamento (calculado)
```

- Uma **Pessoa** pode ter multiplos vinculos com municipios (prefeito, secretario, etc.)
- Um **Municipio** tem registros anuais de **Adimplencia** e um score de **Engajamento** por bienio
- Um **Evento** gera **Participacoes** que alimentam o engajamento do municipio vinculado
- O **Engajamento** e recalculado automaticamente via Django signals

---

## Stack e Dependencias

| Camada      | Tecnologia                 | Versao   |
|-------------|----------------------------|----------|
| Linguagem   | Python                     | 3.12+    |
| Framework   | Django                     | 5.1.x    |
| Banco       | SQLite (dev) / PostgreSQL  | 16       |
| Admin       | Django Unfold              | latest   |
| Frontend    | Tailwind CSS (CDN)         | 3.x      |
| Interacao   | HTMX                       | 2.0.4    |
| Reatividade | Alpine.js                  | 3.x      |
| Icones      | Lucide Icons               | latest   |
| Mapas       | Leaflet.js                 | 1.9.4    |
| Fonte       | Inter (Google Fonts)       | -        |

**Nao usar:** Docker, Celery, Redis. Desenvolvimento 100% local, tarefas sincronas.

---

## Estrutura de Diretorios

```
Sistema-FNP/
├── configuracao/                 # Settings Django
│   ├── base.py                   #   Configuracoes compartilhadas
│   ├── local.py                  #   Dev (SQLite, DEBUG=True)
│   ├── producao.py               #   Producao (PostgreSQL, SSL)
│   ├── urls.py                   #   Roteamento raiz
│   ├── wsgi.py / asgi.py         #   Entry points WSGI/ASGI
│   └── __init__.py
│
├── aplicacoes/                   # Apps Django
│   ├── nucleo/                   #   Base: ModeloBase, Perfil, LogAlteracao, auth
│   │   ├── models.py             #     ModeloBase (abstract), Perfil, LogAlteracao
│   │   ├── views.py              #     inicio (dashboard), entrar, sair
│   │   ├── urls.py               #     /, /entrar/, /sair/
│   │   ├── admin.py              #     UserAdmin + PerfilInline, LogAlteracaoAdmin
│   │   ├── apps.py               #     default_auto_field = BigAutoField
│   │   ├── context_processors.py #     perfil_usuario → eh_editor
│   │   ├── templatetags/
│   │   │   └── fnp_tags.py       #     avatar_pessoa, brasao_municipio
│   │   ├── servicos/
│   │   │   └── auditoria.py      #     registrar_criacao/edicao/exclusao, detectar_alteracoes
│   │   └── management/commands/
│   │       └── popular_mockup.py #     Seed com dados reais de demonstracao
│   │
│   ├── cadastro/                 #   Pessoa, Municipio, VinculoMunicipio, Pauta
│   │   ├── models.py             #     5 models (ver Modelo de Dados)
│   │   ├── views.py              #     CRUD pessoas e municipios + busca HTMX
│   │   ├── urls.py               #     8 rotas (lista/detalhe/criar/editar)
│   │   ├── forms.py              #     PessoaForm, MunicipioForm (ModelForm)
│   │   └── admin.py              #     Unfold admin com inlines
│   │
│   ├── adimplencia/              #   Controle de pagamentos
│   │   ├── models.py             #     Adimplencia (status anual por municipio)
│   │   ├── views.py              #     lista_adimplencia + busca HTMX
│   │   ├── urls.py               #     1 rota
│   │   └── admin.py              #     Unfold admin
│   │
│   ├── engajamento/              #   Pontuacao e ranking
│   │   ├── models.py             #     ConfiguracaoEngajamento (singleton), Engajamento
│   │   ├── views.py              #     lista_engajamento + busca HTMX
│   │   ├── urls.py               #     1 rota
│   │   ├── signals.py            #     Recalcula engajamento em post_save/post_delete
│   │   └── admin.py              #     Unfold admin, campos read-only
│   │
│   ├── eventos/                  #   Eventos e participacoes
│   │   ├── models.py             #     Evento, Participacao (calcula pontos no save)
│   │   ├── views.py              #     lista_eventos, detalhe_evento + busca HTMX
│   │   ├── urls.py               #     2 rotas
│   │   └── admin.py              #     Unfold admin com ParticipacaoInline
│   │
│   └── relatorios/               #   Dashboards (placeholder)
│       ├── views.py              #     painel (stub)
│       └── urls.py               #     1 rota
│
├── templates/                    # Templates Jinja/DTL
│   ├── base.html                 #   Layout principal (sidebar, header, content)
│   ├── nucleo/
│   │   ├── entrar.html           #   Tela de login (standalone, sem base.html)
│   │   └── inicio.html           #   Dashboard com KPIs
│   ├── cadastro/
│   │   ├── lista_pessoas.html         # Listagem com busca HTMX
│   │   ├── detalhe_pessoa.html        # Perfil completo
│   │   ├── form_pessoa.html           # Formulario criar/editar
│   │   ├── lista_municipios.html
│   │   ├── detalhe_municipio.html     # Com mapa Leaflet
│   │   ├── form_municipio.html
│   │   └── parciais/                  # Fragmentos HTMX (so tabela)
│   │       ├── lista_pessoas_tabela.html
│   │       └── lista_municipios_tabela.html
│   ├── adimplencia/
│   │   ├── lista_adimplencia.html
│   │   └── parciais/lista_adimplencia_tabela.html
│   ├── engajamento/
│   │   ├── lista_engajamento.html
│   │   └── parciais/lista_engajamento_tabela.html
│   ├── eventos/
│   │   ├── lista_eventos.html
│   │   ├── detalhe_evento.html
│   │   └── parciais/lista_eventos_tabela.html
│   └── relatorios/
│       └── painel.html
│
├── estaticos/                    # Arquivos estaticos (CSS, JS, imagens)
│   ├── img/
│   │   ├── logo-fnp.png          #   Logo institucional
│   │   └── brasoes/              #   Brasoes baixados do Wikimedia (por cod IBGE)
│   ├── css/.gitkeep
│   └── js/.gitkeep
│
├── media/                        # Uploads de usuario (nao commitado)
│   ├── pessoas/fotos/            #   Fotos de pessoas
│   └── municipios/brasoes/       #   Brasoes enviados pelo editor
│
├── documentacao/                 # Documentacao do projeto
│   ├── arquitetura/              #   Diagramas e docs tecnicos
│   ├── screenshots/              #   Screenshots para apresentacao
│   ├── manual-do-usuario.md      #   Guia do usuario final
│   └── Guia-Sistema-FNP.pptx    #   Apresentacao PowerPoint
│
├── requisitos/
│   └── base.txt                  # Dependencias Python
│
├── manage.py                     # Entry point Django
├── CLAUDE.md                     # Instrucoes para AI assistente
└── CHECKLIST.md                  # Checklist de implementacao
```

---

## Configuracao (Settings)

### `configuracao/base.py`

Configuracoes compartilhadas entre ambientes.

| Configuracao         | Valor                          | Notas                         |
|----------------------|--------------------------------|-------------------------------|
| `INSTALLED_APPS`     | unfold + django + 6 apps locais | Unfold deve vir antes do admin |
| `STATIC_URL`         | `/estaticos/`                  | Servido pelo Django em dev    |
| `MEDIA_URL`          | `/media/`                      | Uploads de usuario            |
| `LOGIN_URL`          | `/entrar/`                     | Redireciona para login        |
| `DEFAULT_AUTO_FIELD` | `BigAutoField`                 | Models sem UUID usam BigInt   |
| Context Processor    | `perfil_usuario`               | Injeta `eh_editor` nos templates |

### `configuracao/local.py`

- `DEBUG = True`
- Banco: **SQLite** (`db.sqlite3`)
- Email: Console backend

### `configuracao/producao.py`

- `DEBUG = False`
- Banco: **PostgreSQL 16** (variaveis de ambiente)
- Seguranca: SSL redirect, HSTS, cookies seguros

### `configuracao/urls.py`

```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('aplicacoes.nucleo.urls')),
    path('cadastro/', include('aplicacoes.cadastro.urls')),
    path('adimplencia/', include('aplicacoes.adimplencia.urls')),
    path('engajamento/', include('aplicacoes.engajamento.urls')),
    path('eventos/', include('aplicacoes.eventos.urls')),
    path('relatorios/', include('aplicacoes.relatorios.urls')),
]
# + static(MEDIA_URL) em DEBUG
```

---

## Aplicacoes

### nucleo

**Responsabilidade:** modelo base abstrato, autenticacao, perfis de acesso,
auditoria, template tags, dashboard.

**Models:**

- `ModeloBase` — abstrato. UUID pk, `criado_em` (auto_now_add), `atualizado_em` (auto_now). Todos os models do projeto herdam dele.
- `Perfil` — OneToOne com `auth.User`. Campo `tipo` com choices: `visualizador`, `editor`. Property `eh_editor`.
- `LogAlteracao` — Registro de auditoria. Campos: `usuario` (FK nullable), `acao` (criacao/edicao/exclusao), `modelo`, `objeto_id`, `objeto_repr`, `campos_alterados` (JSONField com `{campo: {antes, depois}}`), `data`.

**Servicos:**

`aplicacoes/nucleo/servicos/auditoria.py`:

```python
registrar_criacao(usuario, objeto)           # Cria log de criacao
registrar_edicao(usuario, objeto, alteracoes) # Cria log com diff dos campos
registrar_exclusao(usuario, objeto)          # Cria log de exclusao
detectar_alteracoes(objeto, dados_novos)     # Retorna dict {campo: {antes, depois}}
```

**Template Tags** (`fnp_tags.py`):

```python
{% load fnp_tags %}
{% avatar_pessoa pessoa 150 as url %}    # foto upload > pravatar.cc
{% brasao_municipio municipio as url %}  # brasao upload > estatico > DiceBear
```

Ordem de prioridade para imagens:
1. Arquivo enviado pelo editor (campo ImageField)
2. Arquivo estatico local (brasoes do Wikimedia em `estaticos/img/brasoes/{ibge}.svg`)
3. Servico externo de fallback (pravatar.cc para pessoas, DiceBear para municipios)

**Context Processor** (`context_processors.py`):

Injeta `eh_editor` (bool) em todos os templates. True se `user.is_superuser` ou `user.perfil.eh_editor`.

---

### cadastro

**Responsabilidade:** CRUD de pessoas, municipios, vinculos e pautas.

**Models:**

| Model              | Campos principais                                                        | Relacoes                              |
|--------------------|--------------------------------------------------------------------------|---------------------------------------|
| `Pessoa`           | nome, email (unique), telefone, foto, tipo, cargo, partido, genero, mandato_inicio/fim, ativo | vinculos → Municipio, participacoes → Evento |
| `Municipio`        | nome, uf, codigo_ibge (unique), populacao, regiao, brasao, eh_capital, associado_fnp, lat/lng | vinculos → Pessoa, adimplencias, engajamentos, participacoes |
| `Pauta`            | nome (unique), descricao, icone, ativa                                   | envolvimentos → Pessoa                |
| `EnvolvimentoPauta`| nivel (apoiador/engajado/lider), observacao                              | FK pessoa, FK pauta. Unique(pessoa, pauta) |
| `VinculoMunicipio` | papel, inicio/fim_mandato, vigente, observacao                           | FK pessoa, FK municipio. Unique(pessoa, municipio, papel, inicio_mandato) |

**Tipos de Pessoa:** `interno`, `prefeito`, `vice_prefeito`, `secretario`, `assessor`, `vereador`, `outro`

**Papeis no Vinculo:** `prefeito`, `vice_prefeito`, `secretario`, `assessor`, `vereador`, `contato`

**Views:**

Todas protegidas com `@login_required`. Helper `_eh_editor(request)` para checar permissao de escrita.

| View              | Metodo  | Rota                              | Permissao   |
|-------------------|---------|-----------------------------------|-------------|
| lista_pessoas     | GET     | `/cadastro/pessoas/`              | Autenticado |
| detalhe_pessoa    | GET     | `/cadastro/pessoas/<uuid>/`       | Autenticado |
| criar_pessoa      | GET/POST| `/cadastro/pessoas/novo/`         | Editor      |
| editar_pessoa     | GET/POST| `/cadastro/pessoas/<uuid>/editar/`| Editor      |
| lista_municipios  | GET     | `/cadastro/municipios/`           | Autenticado |
| detalhe_municipio | GET     | `/cadastro/municipios/<uuid>/`    | Autenticado |
| criar_municipio   | GET/POST| `/cadastro/municipios/novo/`      | Editor      |
| editar_municipio  | GET/POST| `/cadastro/municipios/<uuid>/editar/` | Editor  |

**Busca HTMX:** todas as views de lista verificam `request.headers.get('HX-Request')`. Se verdadeiro, retornam apenas o fragmento da tabela (`parciais/`). O input de busca usa `hx-get` com `hx-trigger="keyup changed delay:300ms"`.

**Upload de arquivos:** forms usam `enctype="multipart/form-data"` e views passam `request.FILES`.

---

### adimplencia

**Responsabilidade:** Registro anual de pagamentos dos municipios.

**Model:**

```
Adimplencia
├── municipio (FK Municipio)
├── ano_referencia (int)
├── status: adimplente | inadimplente | parcial
├── valor_devido (Decimal 12,2)
├── valor_pago (Decimal 12,2)
├── data_pagamento (Date, nullable)
└── observacao (Text)
Unique: (municipio, ano_referencia)
```

**Impacto:** ao salvar uma Adimplencia, o signal `post_save` em `engajamento/signals.py` recalcula o engajamento do municipio (penalidade de 30% para inadimplente, 15% para parcial).

---

### engajamento

**Responsabilidade:** Calcular e manter o score de engajamento dos municipios.

**Models:**

`ConfiguracaoEngajamento` — **Singleton**. Garante apenas um registro via override de `save()`.

| Campo                    | Default | Descricao                                        |
|--------------------------|---------|--------------------------------------------------|
| bienio_atual             | 2025-2026 | Bienio vigente                                 |
| meta_bienio              | 200     | Meta fixa (nao usada mais — ver meta dinamica)   |
| fator_decaimento         | 0.70    | Pontos do ano anterior multiplicados por 70%     |
| penalidade_inadimplente  | 0.30    | Perde 30% se inadimplente                        |
| penalidade_parcial       | 0.15    | Perde 15% se parcial                             |

`Engajamento` — Score por municipio/bienio. Unique(municipio, bienio).

**Algoritmo de calculo (`recalcular()`):**

```
1. Buscar todos os Eventos do bienio (ano1, ano2)
2. META DINAMICA = soma(evento.pontos_presencial) de todos os eventos
3. Buscar Participacoes confirmadas do municipio no bienio
4. pontos_ano1 = soma(pontos_calculados) das participacoes do ano1
5. pontos_ano2 = soma(pontos_calculados) das participacoes do ano2
6. Se ano_atual >= ano2:
     pontuacao_bruta = pontos_ano2 + (pontos_ano1 * fator_decaimento)
   Senao:
     pontuacao_bruta = pontos_ano1
7. Buscar Adimplencia do municipio no ano_atual
8. penalidade = pontuacao_bruta * percentual_penalidade
9. pontuacao_liquida = pontuacao_bruta - penalidade
10. pontuacao_normalizada = min(100, (pontuacao_liquida / META_DINAMICA) * 100)
11. Classificar nivel:
      >= 70 → Alto
      >= 40 → Medio
      >= 10 → Baixo
      < 10  → Inativo
12. Salvar
```

**Por que meta dinamica?** Se existem 3 eventos no bienio valendo 10 pts cada (total 30), um municipio que participou presencialmente dos 3 tem score 100/100. Isso e mais justo que uma meta fixa de 200 quando ha poucos eventos cadastrados.

**Signals** (`signals.py`):

| Signal      | Sender        | Acao                                   |
|-------------|---------------|----------------------------------------|
| post_save   | Participacao  | Recalcula engajamento do municipio     |
| post_delete | Participacao  | Recalcula engajamento do municipio     |
| post_save   | Adimplencia   | Recalcula engajamento (atualiza penalidade) |

---

### eventos

**Responsabilidade:** Registro de eventos e participacoes.

**Models:**

`Evento`:

| Campo                    | Tipo    | Descricao                        |
|--------------------------|---------|----------------------------------|
| titulo                   | Char    |                                  |
| tipo                     | Choice  | 9 tipos (reuniao_geral, forum, congresso, etc.) |
| modalidade               | Choice  | presencial, online, hibrido      |
| data_inicio / data_fim   | Date    | data_fim nullable                |
| local                    | Char    |                                  |
| pontos_presencial        | Int     | Default 10                       |
| pontos_online            | Int     | Default 5                        |
| pontos_palestrante_bonus | Int     | Default 5                        |
| pontos_organizador_bonus | Int     | Default 5                        |

`Participacao`:

| Campo              | Tipo    | Descricao                                |
|--------------------|---------|------------------------------------------|
| pessoa             | FK      | Quem participou                          |
| evento             | FK      | De qual evento                           |
| municipio          | FK      | Qual municipio recebe os pontos          |
| forma_participacao | Choice  | presencial, online                       |
| papel_no_evento    | Choice  | participante, palestrante, organizador, moderador |
| confirmado         | Bool    | So gera pontos se True                   |
| pontos_calculados  | Int     | Calculado automaticamente no save()      |

**Calculo de pontos** (`calcular_pontos()`):

```python
base = pontos_presencial se presencial, senao pontos_online
if palestrante: base += pontos_palestrante_bonus
if organizador: base += pontos_organizador_bonus
```

O `save()` da Participacao chama `calcular_pontos()` antes de salvar. Apos salvar, o signal recalcula o engajamento do municipio.

---

### relatorios

**Status:** Placeholder. Sera implementado na Fase 5 (dashboards Chart.js, exportacao PDF/Excel).

---

## Modelo de Dados

```
                    ┌──────────────┐
                    │   Pessoa     │
                    │──────────────│
                    │ nome         │
                    │ tipo         │
                    │ foto         │
                    │ partido      │
                    │ mandato_*    │
                    │ ativo        │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼───┐  ┌─────▼──────┐  ┌──▼───────────────┐
     │ Vinculo    │  │Envolvimento│  │  Participacao     │
     │ Municipio  │  │  Pauta     │  │──────────────────│
     │────────────│  │────────────│  │ forma_participacao│
     │ papel      │  │ nivel      │  │ papel_no_evento  │
     │ vigente    │  └─────┬──────┘  │ confirmado       │
     │ mandato_*  │        │         │ pontos_calculados │
     └────────┬───┘  ┌─────▼──────┐  └──┬──────────┬────┘
              │      │   Pauta    │     │          │
              │      └────────────┘     │          │
     ┌────────▼───────┐          ┌──────▼───┐  ┌───▼─────┐
     │   Municipio    │          │  Evento   │  │Municipio│
     │────────────────│          │───────────│  │(pontos) │
     │ nome, uf       │          │ titulo    │  └─────────┘
     │ codigo_ibge    │          │ tipo      │
     │ brasao         │          │ modalidade│
     │ populacao      │          │ pontos_*  │
     │ associado_fnp  │          └───────────┘
     │ lat/lng        │
     └──────┬─────────┘
            │
   ┌────────┼────────────┐
   │                     │
┌──▼──────────┐  ┌───────▼──────┐
│ Adimplencia │  │ Engajamento  │
│─────────────│  │──────────────│
│ ano_ref     │  │ bienio       │
│ status      │  │ pont_bruta   │
│ valor_*     │  │ pont_norm    │
└─────────────┘  │ nivel        │
                 └──────────────┘
```

Todos os models herdam de `ModeloBase` (UUID pk, criado_em, atualizado_em).

---

## Autenticacao e Permissoes

### Perfis

| Perfil        | Login | Ver dados | Criar/Editar | Django Admin | Gerenciar usuarios |
|---------------|-------|-----------|--------------|-------------|-------------------|
| Visualizador  | Sim   | Sim       | Nao          | Nao         | Nao               |
| Editor        | Sim   | Sim       | Sim          | Nao         | Nao               |
| Superusuario  | Sim   | Sim       | Sim          | Sim         | Sim               |

### Implementacao

1. `Perfil` model (OneToOne com User, campo `tipo`)
2. `context_processors.perfil_usuario` injeta `eh_editor` em todos os templates
3. Views usam `@login_required` + helper `_eh_editor(request)`
4. Templates condicionam botoes com `{% if eh_editor %}`
5. Superusuario e tratado como editor automaticamente (`is_superuser` → `eh_editor = True`)
6. Django Admin (`/admin/`) acessivel apenas para `is_staff=True`

### Fluxo de login

```
GET /qualquer-pagina/
  → @login_required redireciona para /entrar/?next=/qualquer-pagina/
  → Usuario preenche form
  → POST /entrar/ → authenticate() → login() → redirect(next)
```

---

## Auditoria

Toda criacao e edicao feita por um editor gera um registro em `LogAlteracao`.

### Estrutura do log de edicao

```json
{
  "usuario": "editor",
  "acao": "edicao",
  "modelo": "Pessoa",
  "objeto_id": "uuid-...",
  "objeto_repr": "Carlos Mendonca",
  "campos_alterados": {
    "cargo": {
      "antes": "Prefeito",
      "depois": "Prefeito Municipal"
    },
    "partido": {
      "antes": "PSD",
      "depois": "MDB"
    }
  },
  "data": "2026-03-25T14:30:00Z"
}
```

### Onde consultar

- **Superusuario:** Django Admin → Nucleo → Logs de alteracao
- Filtros: por acao, modelo, data
- Busca: por nome do objeto ou usuario
- Logs sao **read-only** (ninguem pode editar ou criar manualmente)

### Como registrar em novas views

```python
from aplicacoes.nucleo.servicos.auditoria import (
    detectar_alteracoes, registrar_criacao, registrar_edicao
)

# Criacao
objeto = form.save()
registrar_criacao(request.user, objeto)

# Edicao
alteracoes = detectar_alteracoes(objeto, form.cleaned_data)
form.save()
registrar_edicao(request.user, objeto, alteracoes)
```

---

## Motor de Engajamento

### Fluxo completo

```
Editor registra Participacao (confirmada)
  → Participacao.save() calcula pontos
  → Signal post_save dispara
  → _recalcular_engajamento_municipio()
  → Engajamento.recalcular()
    → Busca meta dinamica (soma pontos presencial de todos os eventos)
    → Soma pontos do municipio (com decaimento do ano anterior)
    → Aplica penalidade de adimplencia
    → Normaliza para 0-100
    → Classifica nivel
    → Salva
```

### Exemplo numerico

```
Eventos do bienio 2025-2026:
  - Reuniao Geral: 10 pts presencial
  - Forum: 10 pts presencial
  - Webinar: 5 pts presencial (so online)
  META DINAMICA = 10 + 10 + 5 = 25

Municipio "Sao Paulo":
  - Participou presencial da Reuniao: 10 pts
  - Participou online do Forum: 5 pts
  - Nao participou do Webinar: 0 pts
  PONTUACAO BRUTA = 15

  Adimplencia: adimplente → penalidade = 0
  PONTUACAO LIQUIDA = 15

  NORMALIZADA = min(100, (15 / 25) * 100) = 60
  NIVEL = Medio (>=40 e <70)
```

---

## Frontend e Templates

### Padrao de busca HTMX

Toda pagina de listagem segue o mesmo padrao:

```html
<!-- Template principal (lista_X.html) -->
<input hx-get="{% url 'app:lista_X' %}"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#tabela-X"
       hx-include="this"
       name="busca">

<div id="tabela-X">
    {% include "app/parciais/lista_X_tabela.html" %}
</div>
```

```python
# View
def lista_X(request):
    busca = request.GET.get('busca', '').strip()
    qs = Model.objects.all()
    if busca:
        qs = qs.filter(Q(campo__icontains=busca) | ...)
    template = 'parciais/...' if request.headers.get('HX-Request') else 'lista_...'
    return render(request, template, {'objetos': qs, 'busca': busca})
```

### Template tags customizadas

Carregar em qualquer template:
```html
{% load fnp_tags %}
{% avatar_pessoa pessoa 64 as foto %}
{% brasao_municipio municipio as brasao %}
```

### Convencao de templates

```
templates/<app>/<acao>_<entidade>.html          # Pagina completa
templates/<app>/parciais/<nome_parcial>.html    # Fragmento HTMX
templates/<app>/form_<entidade>.html            # Formulario criar/editar
```

### Mapa Leaflet (detalhe_municipio)

Carregado via CDN. Usa coordenadas do model. Se nao tem coordenadas, mostra mapa do Brasil (zoom 4). JS no bloco `{% block js_extra %}` com `invalidateSize()` apos layout carregar.

---

## Rotas (URLs)

| Rota                                 | View                | App          |
|--------------------------------------|---------------------|--------------|
| `/`                                  | inicio              | nucleo       |
| `/entrar/`                           | entrar              | nucleo       |
| `/sair/`                             | sair                | nucleo       |
| `/admin/`                            | Django Admin        | admin        |
| `/cadastro/pessoas/`                 | lista_pessoas       | cadastro     |
| `/cadastro/pessoas/novo/`            | criar_pessoa        | cadastro     |
| `/cadastro/pessoas/<uuid>/`          | detalhe_pessoa      | cadastro     |
| `/cadastro/pessoas/<uuid>/editar/`   | editar_pessoa       | cadastro     |
| `/cadastro/municipios/`              | lista_municipios    | cadastro     |
| `/cadastro/municipios/novo/`         | criar_municipio     | cadastro     |
| `/cadastro/municipios/<uuid>/`       | detalhe_municipio   | cadastro     |
| `/cadastro/municipios/<uuid>/editar/`| editar_municipio    | cadastro     |
| `/adimplencia/`                      | lista_adimplencia   | adimplencia  |
| `/engajamento/`                      | lista_engajamento   | engajamento  |
| `/eventos/`                          | lista_eventos       | eventos      |
| `/eventos/<uuid>/`                   | detalhe_evento      | eventos      |
| `/relatorios/`                       | painel              | relatorios   |

---

## Comandos de Gestao

```bash
# Desenvolvimento
python manage.py runserver              # Inicia servidor dev
python manage.py popular_mockup         # Popula banco com dados reais de demo
python manage.py createsuperuser        # Cria superusuario

# Migracao
python manage.py makemigrations         # Gera migracoes
python manage.py migrate                # Aplica migracoes

# Testes
python manage.py test aplicacoes/       # Roda testes
python manage.py check                  # Verifica configuracao
```

---

## Convencoes de Codigo

### Idioma

- **PT-BR**: nomes de apps, models, campos, URLs, templates, variaveis de negocio
- **Ingles**: nomes tecnicos do Django (`models.py`, `views.py`, `urls.py`, `forms.py`)

### Models

- Sempre herdar de `ModeloBase` (UUID pk, timestamps)
- Campos de data: `criado_em`, `atualizado_em` (automaticos)
- `__str__` retorna representacao legivel
- `class Meta` com `verbose_name` e `verbose_name_plural`
- Logica de negocio complexa vai em `servicos/`, nao no model

### Views

- `@login_required` em todas as views autenticadas
- Verificar `_eh_editor()` antes de operacoes de escrita
- Registrar auditoria em toda criacao/edicao
- Suportar HTMX verificando `HX-Request` header

### Templates

- `templates/<app>/<acao>_<entidade>.html`
- Fragmentos HTMX em `templates/<app>/parciais/`
- Sempre usar `{% load fnp_tags %}` quando precisar de avatar/brasao
- Forms com `enctype="multipart/form-data"` quando ha upload

### Imports

- Absolutos: `from aplicacoes.cadastro.models import Pessoa`
- Nunca usar imports relativos

---

## Decisoes de Projeto (ADRs)

### ADR-001: UUID como chave primaria

**Decisao:** todos os models usam UUID v4 como pk.
**Motivo:** evita exposicao de sequencia numerica nas URLs, facilita merge de dados entre ambientes.
**Impacto:** URLs mais longas, mas mais seguras.

### ADR-002: Meta dinamica de engajamento

**Decisao:** a meta para normalizar o score de engajamento e calculada dinamicamente (soma dos pontos presenciais de todos os eventos do bienio), nao um valor fixo.
**Motivo:** com poucos eventos cadastrados, uma meta fixa de 200 pontos faria todos os municipios parecerem inativos. A meta dinamica garante que participar de todos os eventos = 100%.
**Impacto:** o campo `meta_bienio` na `ConfiguracaoEngajamento` nao e mais usado no calculo.

### ADR-003: Signals para recalculo automatico

**Decisao:** usar Django signals (`post_save`, `post_delete`) para recalcular engajamento automaticamente.
**Motivo:** garante consistencia sem depender de tarefas asincronas (Celery proibido no projeto).
**Risco:** pode ficar lento com muitas participacoes. Mitigacao: o recalculo e por municipio, nao global.

### ADR-004: Auditoria via servico, nao middleware

**Decisao:** a auditoria e registrada explicitamente nas views via `servicos/auditoria.py`, nao por middleware automatico.
**Motivo:** controle fino sobre quais operacoes geram log. O Django Admin ja tem seu proprio historico.
**Impacto:** toda nova view de escrita precisa chamar `registrar_criacao/edicao` manualmente.

### ADR-005: Imagens com fallback em cascata

**Decisao:** template tags (`avatar_pessoa`, `brasao_municipio`) verificam: upload do editor → arquivo estatico → servico externo.
**Motivo:** garante que o sistema sempre mostra uma imagem, mesmo sem upload, enquanto permite que o editor substitua por imagens reais.
**Impacto:** dependencia de servicos externos (pravatar.cc, DiceBear) para fallback, mas funciona offline com os uploads.

### ADR-006: HTMX para busca em tempo real

**Decisao:** busca nas listagens via HTMX com debounce de 300ms, retornando fragmentos HTML.
**Motivo:** UX responsiva sem SPA, mantendo a simplicidade do Django templates.
**Impacto:** cada view de lista precisa suportar dois templates (completo e parcial).

### ADR-007: Sem Docker

**Decisao:** desenvolvimento 100% local, sem Docker.
**Motivo:** decisao institucional da equipe. Simplifica setup para devs nao familiarizados com containers.
**Impacto:** cada dev precisa instalar Python, PostgreSQL (ou usar SQLite em dev) localmente.
