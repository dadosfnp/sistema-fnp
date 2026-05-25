# Sistema FNP

Plataforma web de gestão institucional da Frente Nacional de Prefeitos.
Cadastro de pessoas (prefeitos, secretários, equipe interna), municípios,
adimplência, engajamento, eventos, missões, recepção (visitas) e mala direta.
Compliance LGPD nível 2 (Google OAuth + 2FA + ACL por objeto + auditoria de leitura).

## Stack

- **Django 5.x** + Python 3.12
- **PostgreSQL 16** (Digital Ocean Managed Postgres em produção)
- **HTMX + Tailwind CSS (CDN) + Alpine.js** no front
- **Django Unfold** para o admin
- **django-allauth** (Google OAuth + login local), **django-otp** (2FA TOTP), **django-axes** (brute-force)
- **WhiteNoise** para estáticos em produção
- Stack 100% **síncrono** — sem Celery, sem Redis

## Convenções

- **Idioma:** todo o código de domínio em PT-BR (apps, models, campos, URLs, templates, variáveis de negócio). Nomes técnicos do Django permanecem em inglês (models.py, views.py, urls.py, forms.py, admin.py, manage.py).
- **Estrutura de apps:** cada app fica em `aplicacoes/<nome>/` com models.py, views.py, urls.py, forms.py, admin.py, tests.py
- **Templates:** `templates/<app>/<acao>_<entidade>.html` (ex: `lista_pessoas.html`, `detalhe_municipio.html`). Fragmentos HTMX em `templates/<app>/parciais/`
- **Serviços:** lógica de negócio que não pertence ao model nem à view fica em `aplicacoes/<app>/servicos/`
- **Imports:** absolutos usando o nome do app (ex: `from aplicacoes.cadastro.models import Pessoa`)

## Comandos básicos

| Comando | Função |
|---|---|
| `python manage.py runserver` | Sobe o dev server (porta 8000) |
| `python manage.py test aplicacoes/` | Roda a suíte (~25 testes) |
| `python manage.py makemigrations` | Gera migrations a partir dos models |
| `python manage.py migrate` | Aplica migrations no banco |
| `python manage.py createsuperuser` | Cria conta admin |
| `python manage.py configurar_google_oauth` | Popula SocialApp Google com base no `.env` (idempotente) |
| `python manage.py purgar_dados_antigos [--dry-run] [--so-anonimizar]` | Purga/anonimiza dados conforme política LGPD |

## Estrutura

```
sistema-fnp/
├── configuracao/          # Settings (base.py, local.py, producao.py) + urls.py
├── aplicacoes/
│   ├── nucleo/            # Perfil, Auth, LGPD, middlewares, permissões
│   ├── cadastro/          # Pessoa, Municipio, VinculoMunicipio
│   ├── adimplencia/       # Pagamentos anuais e status
│   ├── engajamento/       # Pontuação e nível
│   ├── eventos/           # Eventos + Participação
│   ├── instancias/        # Espaços de diálogo federativo
│   ├── projetos/          # Projetos institucionais
│   ├── missoes/           # Missões + delegação
│   ├── atividades/        # Reuniões/atividades por instância
│   ├── documentos/        # Anexos e biblioteca
│   ├── presenca/          # Visitas FNP, pré-credenciamento, presença universal
│   ├── comunicacao/       # Templates de e-mail e mala direta
│   ├── dicionario/        # Glossário do sistema
│   └── relatorios/        # Dashboards e exportações
├── templates/             # Templates globais e por app
├── estaticos/             # CSS, JS
└── documentacao/          # DPIA-RoT, autenticacao-setup, producao-readiness, RDAs
```

## Domínio (núcleo)

- **Pessoa** tem um ou mais **VínculoMunicípio** (prefeito, secretário, assessor)
- **Município** tem registros de **Adimplência** (anual) e **Engajamento** (pontuação)
- **Evento** gera **Participação**, que impacta o engajamento do município
- **Presença** é universal (GenericForeignKey) — anexável a Evento, Missão, Atividade, etc.
- Pontuação de engajamento é recalculada via signals ao registrar participação

## Autenticação e LGPD nível 2

Implementado em commit recente — ler `documentacao/autenticacao-setup.md` para o setup completo.

### Modelo de Perfil (em `aplicacoes/nucleo/models.py`)

`Perfil` tem 3 dimensões combináveis de controle:
- `tipo`: visualizador / editor / admin / prefeito / **externo**
- `municipio_vinculado` (1) + `municipios_visiveis` (M2M, vários)
- `status_aprovacao`: pendente / aprovado / bloqueado / expirado
- `expira_em`: data de expiração (auto-bloqueia depois)
- `requer_2fa`: ligado para externos e admins
- `permissoes_extras`: lista JSON de slugs granulares (`pode_editar`, `pode_ver_dados_lgpd`, etc.)

Permissões por objeto via `PermissaoEntidade` (GenericForeignKey + nível visualizar/editar).

**SEMPRE** usar `aplicacoes.nucleo.servicos.permissoes.pode_ver(user, obj)` em vez de checagens ad-hoc.

### Stack de middlewares (ordem importa — `configuracao/base.py`)

1. `AuthenticationMiddleware` (Django)
2. `OTPMiddleware` (django-otp — injeta `is_verified()`)
3. `AccountMiddleware` (allauth)
4. `IsolarPortalPrefeitoMiddleware` — perfis "prefeito" só ficam em `/portal/`
5. `BloquearAcessoExpiradoMiddleware` — pendente/expirado → `/conta/aguardando-aprovacao/`
6. `Exigir2FAMiddleware` — `requer_2fa=True` → `/conta/2fa/login/`
7. `ExigirAceiteTermoMiddleware` — sem aceite → `/conta/termo-de-uso/`
8. `AxesMiddleware` (último, para capturar sinal de login)

Todos têm bypass automático quando `'test' in sys.argv` para não quebrar a suíte.

### Domínios auto-aprovados

`settings.DOMINIOS_AUTOAPROVADOS = ['fnp.org.br']`. Login Google de `@fnp.org.br` cria perfil aprovado direto. Outros caem em "pendente" + 90 dias de validade + 2FA obrigatório, e ficam em fila no `/admin/nucleo/perfil/`.

### Auditoria

- `LogAlteracao` — CRUD (PII mascarada via `mascarar_pii`)
- `LogAcessoSensivel` — leitura de Pessoa/Visita/CredPrévio via decorator `@registrar_leitura_sensivel`
- `AceiteTermo` — versionado, força re-aceite quando `AceiteTermo.VERSAO_ATUAL` mudar
- `SolicitacaoExclusao` — pedidos LGPD Art. 18 VI

### Comandos LGPD

- `configurar_google_oauth` — após popular GOOGLE_OAUTH_CLIENT_ID/SECRET no `.env`
- `purgar_dados_antigos` — anonimiza Visitas >5 anos + deleta logs >2 anos; rodar mensalmente em prod

## Deploy — Digital Ocean

A FNP migrou para Digital Ocean. Setup oficial:

### Banco de dados (DO Managed PostgreSQL)

1. Painel DO → **Databases → Create** → PostgreSQL 16
2. Plano mínimo recomendado: **Basic $15/mês** (1GB RAM, 10GB SSD) — escala depois
3. Datacenter: **NYC3** ou **SFO3** (latência aceitável para Brasil)
4. Em **Trusted sources**, adicionar o IP do app + IP do dev (ou `0.0.0.0/0` provisoriamente)
5. Copiar a connection string em **Connection Details → Connection string** (formato `postgresql://doadmin:SENHA@cluster.b.db.ondigitalocean.com:25060/defaultdb?sslmode=require`)
6. Colocar no `.env` como `DATABASE_URL=...`

`configuracao/producao.py` já consome `DATABASE_URL` via `dj_database_url.config(ssl_require=True, conn_max_age=600)` — sem ajuste de código.

### App (DO App Platform — recomendado) OU Droplet + gunicorn

**Opção A — App Platform (gerenciado, ~$5/mês Basic):**

1. Painel DO → **Apps → Create App** → conecta o repositório GitHub
2. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
3. Run command: `gunicorn configuracao.wsgi:application --workers 3 --timeout 60`
4. HTTP port: `8000`
5. Variáveis de ambiente (em **App → Settings → Environment Variables**):
   - `DJANGO_SETTINGS_MODULE=configuracao.producao`
   - `SECRET_KEY=...` (gerar com `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
   - `DATABASE_URL=...` (do DO Postgres acima)
   - `ALLOWED_HOSTS=fnp.org.br,sistema.fnp.org.br,.ondigitalocean.app`
   - `GOOGLE_OAUTH_CLIENT_ID=...`, `GOOGLE_OAUTH_CLIENT_SECRET=...`
   - `EMAIL_HOST_USER=...`, `EMAIL_HOST_PASSWORD=...` (SMTP do Google Workspace)
   - `SECURE_SSL_REDIRECT=True`
6. Domínio custom: **Apps → Settings → Domains** → adicionar `sistema.fnp.org.br` e ajustar DNS

**Opção B — Droplet Ubuntu 22.04 + nginx + gunicorn + supervisor:** instruções detalhadas em `documentacao/producao-readiness.md`.

### Pós-deploy (rodar uma única vez)

Via console da App Platform (**Apps → Console**) ou SSH no Droplet:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py configurar_google_oauth        # após GOOGLE_OAUTH_* no .env
python manage.py collectstatic --noinput
```

Cron mensal para a purga LGPD (App Platform → **Jobs → Add Job** type=Cron, schedule=`0 3 1 * *`):
```bash
python manage.py purgar_dados_antigos
```

### Google OAuth no Cloud Console

Passo a passo com URIs corretas para DO em `documentacao/autenticacao-setup.md` §2. Em resumo:
- Authorized JavaScript origins: `https://sistema.fnp.org.br`
- Authorized redirect URIs: `https://sistema.fnp.org.br/accounts/google/login/callback/`

### Mídia (uploads)

App Platform tem filesystem efêmero — uploads desaparecem em cada deploy. Para produção real, migrar `MEDIA_ROOT` para **DO Spaces** (S3-compatível, ~$5/mês) usando `django-storages[boto3]`. Por enquanto, o `producao.py` serve `/media/` via `re_path`, suficiente para validação interna.

## Cuidados

- **Nunca usar Docker** neste projeto — desenvolvimento 100% local; deploy gerenciado.
- **Nunca instalar Celery ou Redis** — tarefas são síncronas. Para jobs periódicos, usar Cron do DO.
- **Sempre usar UUID** como chave primária nos models (via `ModeloBase`).
- **Campos de data:** `criado_em`, `atualizado_em` (gerenciados automaticamente pelo `ModeloBase`).
- **Templates HTMX:** fragmentos parciais retornam apenas HTML, não página completa.
- **Nunca incluir Co-Authored-By do Claude** nos commits — o histórico Git deve mencionar apenas o autor humano.
- **Documentar código (docstrings)** conforme alterando — não esperar pedido.

## Segurança / LGPD

- **NUNCA** ler, exibir ou logar dados pessoais (CPFs, telefones, e-mails de prefeitos/secretários) fora do contexto autorizado.
- **NUNCA** incluir dados reais em fixtures, seeds ou exemplos — sempre dados fictícios.
- Variáveis de ambiente sensíveis ficam **exclusivamente** no `.env` (NUNCA commitado — confira `.gitignore`).
- Antes de adicionar nova categoria de PII: (1) incluir no `purgar_dados_antigos`; (2) incluir no `exportar_meus_dados`; (3) atualizar a seção 3 do `documentacao/DPIA-RoT.md`; (4) considerar aplicar `@registrar_leitura_sensivel` nas views de detalhe.
- DPO oficial: `dpo@fnp.org.br` (placeholder até a FNP designar formalmente).

## Variáveis de ambiente obrigatórias em produção

`producao.py` faz **fail-fast** se faltarem. Mínimo:

| Variável | Para que serve |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `configuracao.producao` |
| `SECRET_KEY` | Mínimo 50 caracteres aleatórios. Gerar com `get_random_secret_key()` |
| `DATABASE_URL` | String do DO Managed Postgres com `?sslmode=require` |
| `ALLOWED_HOSTS` | CSV de domínios permitidos |
| `GOOGLE_OAUTH_CLIENT_ID` | Do Google Cloud Console (Web application) |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Idem |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP do Google Workspace para mala direta |
| `SECURE_SSL_REDIRECT` | `True` em produção |

Template completo em `.env.exemplo` (commitado) — copiar e preencher como `.env` (NÃO commitado).
