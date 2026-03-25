# Sistema FNP

Plataforma web de gestão institucional da Frente Nacional de Prefeitos. Cadastro de pessoas (prefeitos, secretários, equipe interna), municípios, controle de adimplência e engajamento.

## Stack

- Django 5.x + Python 3.12
- PostgreSQL 16
- HTMX + Tailwind CSS + Alpine.js
- Django Unfold (admin)

## Convenções

- **Idioma:** todo o código de domínio em PT-BR (nomes de apps, models, campos, URLs, templates, variáveis de negócio). Nomes técnicos do Django permanecem em inglês (models.py, views.py, urls.py, forms.py, admin.py, manage.py).
- **Estrutura de apps:** cada app fica em `aplicacoes/<nome>/` com models.py, views.py, urls.py, forms.py, admin.py, tests.py
- **Templates:** `templates/<app>/<acao>_<entidade>.html` (ex: `lista_pessoas.html`, `detalhe_municipio.html`). Fragmentos HTMX em `templates/<app>/parciais/`
- **Serviços:** lógica de negócio que não pertence ao model nem à view fica em `aplicacoes/<app>/servicos/`
- **Imports:** absolutos usando o nome do app (ex: `from aplicacoes.cadastro.models import Pessoa`)

## Comandos

- Rodar servidor: `python manage.py runserver`
- Rodar testes: `python manage.py test aplicacoes/`
- Criar migrações: `python manage.py makemigrations`
- Aplicar migrações: `python manage.py migrate`
- Criar superusuário: `python manage.py createsuperuser`

## Estrutura

```
sistema-fnp/
├── configuracao/          # Settings do Django (base.py, local.py, producao.py)
├── aplicacoes/
│   ├── nucleo/            # Mixins, modelo base, autenticação
│   ├── cadastro/          # Pessoa, Municipio, VinculoMunicipio
│   ├── adimplencia/       # Controle de pagamentos e status
│   ├── engajamento/       # Pontuação e nível de engajamento
│   ├── eventos/           # Fóruns, reuniões, participações
│   └── relatorios/        # Dashboards e exportações
├── templates/             # Templates globais e componentes
├── estaticos/             # CSS, JS
└── documentacao/          # Diagramas Mermaid e RDAs
```

## Domínio

- **Pessoa** tem um ou mais **VínculoMunicípio** (prefeito, secretário, assessor)
- **Município** tem registros de **Adimplência** (anual) e **Engajamento** (pontuação)
- **Evento** gera **Participação**, que impacta o engajamento do município vinculado
- Pontuação de engajamento é recalculada via Django signals ao registrar participação

## Cuidados

- Nunca usar Docker neste projeto — desenvolvimento 100% local
- Nunca instalar Celery ou Redis — tarefas são síncronas por enquanto
- Sempre usar UUID como chave primária nos models
- Campos de data: `criado_em`, `atualizado_em` (gerenciados automaticamente)
- Ao criar templates HTMX, fragmentos parciais retornam apenas HTML, não página completa
- name: Nunca incluir Co-Authored-By do Claude
description: Não adicionar Co-Authored-By do Claude nos commits — o usuário não quer que o Claude apareça no histórico do Git

## Segurança

- NUNCA ler, exibir ou logar dados pessoais (telefones, CPFs, emails de prefeitos/secretários)
- NUNCA incluir dados reais em fixtures, seeds ou exemplos — sempre usar dados fictícios
- Variáveis de ambiente sensíveis ficam exclusivamente no .env (nunca commitadas)
- Chave de criptografia do banco: variável CHAVE_CRIPTOGRAFIA no .env