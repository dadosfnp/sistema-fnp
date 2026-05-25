# Plano de produção — Sistema FNP

> Análise para colocar o sistema em produção com **80+ usuários** da equipe FNP
> e tornar a manutenção sustentável a longo prazo.

## Resumo executivo

O sistema está funcional como **MVP visual**, mas tem 4 blocos críticos para
fechar antes do go-live com a equipe completa:

1. **Banco de dados em PostgreSQL gerenciado** (não SQLite)
2. **Armazenamento de mídia em S3/Cloud Storage** (não disco local do Render)
3. **Hardening de segurança** (já documentado em `seguranca-hardening.md`)
4. **Observabilidade** (logs estruturados + monitoramento de erro)

E mais 3 frentes de melhoria que destravam crescimento:
- Performance/cache
- Permissões granulares por equipe/setor
- CI/CD com testes automáticos no PR

---

## 1. Banco de dados — o item mais urgente

### Estado atual

- **Local (dev):** SQLite (`db.sqlite3` no disco)
- **Render (prod):** ainda SQLite por padrão — o `producao.py` tem `dj_database_url.config()` mas só funciona se a env var `DATABASE_URL` estiver setada
- Sem backup automatizado
- Sem replicação
- Sem monitoring de queries lentas

### O que vai dar errado com 80 usuários

1. **SQLite bloqueia a tabela inteira em writes** — qualquer signal de
   recálculo de engajamento congela o sistema para todos os outros enquanto roda.
2. **`db.sqlite3` no Render é efêmero** — cada deploy reseta os dados (já
   acontece hoje, escondido pelos seeds idempotentes).
3. **Não há backup** — se o disco for corrompido ou alguém der `migrate
   --fake-zero`, perde tudo.
4. **Concurrent reads** ficam serializadas — relatórios pesados travam tudo.

### Recomendação

**Postgres 16 no Render** (free tier até 1 GB, mensal $7 para 10 GB).

```bash
# No Render dashboard:
1. New + → PostgreSQL
2. Region: Oregon (mesmo do app)
3. Plan: Starter ($7/mês) ou Free (90 dias)
4. Copia DATABASE_URL → variável de ambiente do app
```

### Configuração de conexão recomendada

```python
# configuracao/producao.py
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ['DATABASE_URL'],
        conn_max_age=600,         # mantém conexão por 10 min (evita overhead)
        conn_health_checks=True,   # Django 4.1+: testa conexão antes de usar
        ssl_require=True,
    )
}

# Pool de conexões — quando passar de 20 usuários simultâneos
DATABASES['default']['OPTIONS'] = {
    'connect_timeout': 10,
    # Em apps com mais de 50 usuários simultâneos, usar django-db-connection-pool
    # ou PgBouncer entre o app e o Postgres.
}
```

### Backup

Render Postgres tem **backup diário automático** (retenção 7 dias no Starter).
Para **point-in-time recovery** e backup off-site:

```bash
# Cron job semanal (GitHub Actions, ou script manual)
pg_dump $DATABASE_URL | gzip > backup-$(date +%Y%m%d).sql.gz
# Sobe para S3 / Google Drive / OneDrive da FNP
```

### Monitoramento

```python
# Em local.py para detectar queries lentas em dev
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'DEBUG' if DEBUG else 'WARNING',
    'propagate': False,
}
```

Em produção, usar **pganalyze** (gratuito até 25 queries/dia) ou
**django-silk** para detectar N+1 e queries pesadas.

---

## 2. Armazenamento de mídia — fotos somem entre deploys

### Problema

Toda foto enviada (`Pessoa.foto`, `Visita.foto`, `CredenciamentoPrevio.foto`,
`Municipio.brasao`, anexos de mala direta) vai para `MEDIA_ROOT` no disco
do container do Render — **disco efêmero**. Cada deploy zera.

### Solução: S3-compatible

**AWS S3** é o padrão. Para a FNP, recomendo **Cloudflare R2** (S3-compatível,
**zero egress fee** — paga só armazenamento, e barato):
- 10 GB grátis/mês
- $0.015/GB depois (vs S3 $0.023)
- Conta Cloudflare grátis basta

```python
# producao.py
INSTALLED_APPS += ['storages']

STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': os.environ['R2_BUCKET'],
            'endpoint_url': os.environ['R2_ENDPOINT'],
            'access_key': os.environ['R2_ACCESS_KEY'],
            'secret_key': os.environ['R2_SECRET_KEY'],
            'querystring_auth': False,  # URLs públicas
            'object_parameters': {'CacheControl': 'max-age=31536000'},
        },
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
MEDIA_URL = f'{os.environ["R2_PUBLIC_URL"]}/'
```

Bônus: **resolve o bug do face-api.js no Render** — R2 retorna CORS corretamente
para `<img crossOrigin>`.

### Migração das fotos existentes

```bash
# Script único — depois de configurar R2, copia o disco do Render
python manage.py shell -c "
from django.core.files.storage import default_storage
import os
for raiz, _, arquivos in os.walk('/var/data/media'):
    for a in arquivos:
        caminho = os.path.relpath(os.path.join(raiz, a), '/var/data/media')
        with open(os.path.join(raiz, a), 'rb') as f:
            default_storage.save(caminho, f)
        print(f'OK {caminho}')
"
```

---

## 3. Hardening de segurança — checklist antes do go-live

Já documentado em `seguranca-hardening.md`. Resumindo os **5 críticos**:

| Item | Onde | Status |
|---|---|---|
| `SECRET_KEY` fail-fast (sem default) | `configuracao/base.py:14` | ❌ |
| Endpoint `/api/busca/` filtrar por perfil | `aplicacoes/nucleo/views.py` | ❌ |
| Validar MIME real de uploads (Pillow.verify + python-magic) | `Pessoa.foto`, `Visita.foto`, anexos | ❌ |
| ModelForm com `fields` explícito (sem `__all__`) | todos os forms.py | ⚠️ revisar |
| Mascarar PII em `LogAlteracao.objeto_repr` | `aplicacoes/nucleo/servicos/auditoria.py` | ❌ |

Plus:
- **CSP** (Content Security Policy) via `django-csp`
- **Rate limit** em `/comunicacao/processar/` e `/api/busca/`
- **JWT com expiração** substituindo Token DRF eterno
- **Validador de slugs** em `Perfil.permissoes_extras`

### LGPD — go-live exige

- [ ] Política de privacidade publicada
- [ ] Termo de uso aceito no primeiro login (já temos no pré-credenciamento, falta no login normal)
- [ ] `/conta/exportar-meus-dados/` (Art. 18 LGPD)
- [ ] `/conta/solicitar-exclusao/` com workflow de aprovação
- [ ] DPO identificado no rodapé do sistema
- [ ] Procedimento de incidente documentado

---

## 4. Permissões para 80+ usuários

### Estado atual

Já temos `Perfil.permissoes_extras` (JSONField) com 7 permissões granulares:
- `pode_editar`, `pode_importar_ibge`, `pode_editar_pesos`, `pode_ver_dados_lgpd`,
  `pode_enviar_email_massa`, `pode_exportar`, `pode_arquivar`

### Falta para escalar

1. **Grupos por departamento** — FNP tem áreas (Comunicação, Jurídico,
   Federativo, Financeiro). Criar `Departamento` model com many-to-many
   com User. Cada departamento herda um conjunto base de permissões.

2. **Auditoria de acesso a dados sensíveis** — registrar quando alguém abre
   o detalhe de uma pessoa (signal post_save no LogAlteracao com `acao='leitura'`).
   Essencial para LGPD.

3. **Convite por e-mail** — formulário "Adicionar funcionário" que envia link
   único pra colaborador setar a senha e aceitar termos. Sem precisar admin
   compartilhar senha temporária.

4. **Quem aprovou quem** — campo `aprovado_por` em Perfil. Quem criou o usuário fica registrado.

### Implementação proposta

```python
class Departamento(ModeloBase):
    """Departamento da FNP — agrupa funcionários com mesmo nível de acesso."""
    nome = models.CharField(max_length=80, unique=True)
    cor = models.CharField(max_length=7, default='#1e3a5f')
    permissoes_default = models.JSONField(default=list)

class Perfil(models.Model):
    ...
    departamentos = models.ManyToManyField(Departamento, blank=True)
    aprovado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
    )

    def pode(self, permissao):
        if self.tipo == 'admin' or self.usuario.is_superuser:
            return True
        if permissao in (self.permissoes_extras or []):
            return True
        # Herda de departamento
        for d in self.departamentos.all():
            if permissao in (d.permissoes_default or []):
                return True
        return False
```

---

## 5. Observabilidade — saber quando algo quebra

### Estado atual

- Logs vão pra stdout do Render (visível no dashboard, retenção 7 dias)
- Sem agregação, sem alertas, sem stack traces estruturadas

### Recomendação: Sentry (gratuito até 5k eventos/mês)

```bash
pip install sentry-sdk
```

```python
# producao.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if os.environ.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.environ['SENTRY_DSN'],
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,      # 10% das requests (performance)
        send_default_pii=False,       # LGPD: não envia user.email
        environment='production',
    )
```

Sentry te dá:
- Stack trace completo de cada erro (variáveis locais incluídas)
- Agrupamento automático de erros similares
- Alerta no Slack/email quando algo novo aparece
- Performance traces (rota X demora Y ms)

### Custom métricas que importam

- Quantidade de visitas registradas por dia
- Latência média do `/relatorios/` (cache hit/miss)
- Quantos pré-credenciamentos viram visita
- Taxa de reconhecimento facial (match/total)

Endpoint `/_status/` que retorna JSON com esses números — passa pra
UptimeRobot fazer ping e gera dashboard.

---

## 6. CI/CD — não dar deploy quebrado

### Hoje

- Push pra master → Render builda e deploya
- Testes existem (25) mas **não rodam no pipeline**
- Não há review obrigatório

### Recomendação

`.github/workflows/ci.yml`:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env: { POSTGRES_PASSWORD: postgres }
        ports: [5432:5432]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - run: python manage.py test --noinput
        env:
          DATABASE_URL: postgres://postgres:postgres@localhost:5432/postgres
          SECRET_KEY: ci-test-key
          DJANGO_SETTINGS_MODULE: configuracao.local
```

Bônus: bloquear merge na main se CI falhar (branch protection no GitHub).

### Cobertura de testes — onde estamos vs onde devemos chegar

Temos **25 testes em cadastro**. Falta:
- ⚠️ Testes em **engajamento** (cálculo, recálculo via signals)
- ⚠️ Testes em **adimplência**
- ⚠️ Testes em **relatórios** (endpoints JSON do mapa, painel)
- ⚠️ Testes em **comunicação** (mala direta + WhatsApp links)
- ⚠️ Testes em **presença** (visita + pré-credenciamento + identificação)

Meta razoável: **70% de cobertura** medida com `coverage.py`.

---

## 7. Performance — o que vai ficar lento com 5.570 municípios

### Já feito

- ✅ Índices em campos filtráveis (`Pessoa.nome`, `Municipio.uf`, etc.)
- ✅ Cache de 60s no `/relatorios/`
- ✅ Paginação 50/pg em pessoas e municípios
- ✅ HTMX para partial reloads

### Próximas otimizações

1. **`select_related` / `prefetch_related`** auditados — pode ter N+1 em
   `lista_municipios` quando exibe adimplência atual. Mediar com `django-silk`.

2. **`django.contrib.postgres` aggregates** quando migrar pra PG:
   - `JSONField` para queries em `permissoes_extras`
   - `ArrayField` para tags/categorias
   - Full-text search (`SearchVector`) em vez de `icontains` quando passar de 10k pessoas

3. **Compressão** de respostas:
   - `gzip_middleware` já vem com WhiteNoise pros assets
   - Para HTML, adicionar `django.middleware.gzip.GZipMiddleware`

4. **CDN para assets**:
   - WhiteNoise serve bem até ~50 req/s, depois Cloudflare na frente

---

## 8. Mobile / acessibilidade

A maior parte do uso (especialmente recepção e portal externo dos prefeitos)
vai ser mobile. Auditar:

- [ ] Tap targets ≥ 44px (Apple HIG) — alguns botões pequenos atualmente
- [ ] Contraste mínimo 4.5:1 (WCAG AA) — verificar dark mode
- [ ] `aria-label` em ícones sem texto (botões só com lucide-icon)
- [ ] Navegação por teclado (Tab/Shift+Tab) funciona em modais HTMX?
- [ ] `lang="pt-br"` em todos os templates ✓ (já tem)
- [ ] `prefers-reduced-motion` respeitado nas animações

Ferramenta: rodar Lighthouse no Chrome DevTools em 5 páginas-chave.

---

## 9. Manutenibilidade a longo prazo

### Bom estado

- ✅ Convenções PT-BR documentadas em CLAUDE.md
- ✅ RDAs em `documentacao/arquitetura/decisoes/`
- ✅ Services pattern aplicado em vários módulos
- ✅ Models organizados em pacote (cadastro/models/)

### Pontos de atenção

1. **Documentação operacional** está só no código. Falta:
   - `documentacao/runbook.md` — "como restaurar backup", "como rotacionar SECRET_KEY",
     "o que fazer se o seed quebrar"
   - `documentacao/onboarding-dev.md` — "como rodar localmente em 5 minutos"

2. **Pre-commit hooks** ajudariam o time a manter padrão:
   ```yaml
   # .pre-commit-config.yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.5.0
       hooks: [{id: ruff, args: [--fix]}, {id: ruff-format}]
   ```

3. **Versioning das migrations** — quando dois devs criam migration em
   paralelo, conflito. Convenção: sempre `git pull` antes de
   `makemigrations`; se conflitar, `python manage.py migrate --fake <app>
   <ultima_migration_main>` e refazer.

4. **Roadmap visível** — usar GitHub Projects ou linear.app para
   priorização visível à equipe FNP.

---

## 10. Features para 80+ usuários — o que está faltando

### Curto prazo (próximas 2 semanas)

- [ ] **Notificações in-app em tempo real** — WebSocket via django-channels
  ou polling HTMX já implementado, mas falta indicação visual no badge
- [ ] **Onboarding tour para novos funcionários** — já existe, expandir
  com mais telas-chave
- [ ] **Filtros salvos compartilháveis** — hoje são pessoais; adicionar
  flag "público" para visões da equipe
- [ ] **Exportação assíncrona** — relatórios grandes não bloqueiam request
- [ ] **Auditoria de leitura** de dados sensíveis (LGPD)

### Médio prazo (próximo trimestre)

- [ ] **Sincronização Google Calendar** (ver seção 11)
- [ ] **Portal externo dos prefeitos** — já temos esqueleto em `/portal/`,
  falta migração + envio de credenciais
- [ ] **WhatsApp Cloud API** — quando volume passar de 100 msgs/semana
- [ ] **Dashboard customizável** — cada departamento monta a sua home
- [ ] **Busca full-text em documentos** — extrair texto de PDFs via `pdfplumber`

### Longo prazo (6+ meses)

- [ ] **App mobile (PWA otimizado)** — recepção em tablet, prefeitos em iOS/Android
- [ ] **BI em PowerBI/Looker** — conectado via API REST que já temos
- [ ] **AI assistant** — buscar respostas no dicionário + histórico via embedding
- [ ] **Workflow de aprovação** — projetos/missões com etapas + signatures

---

## 11. Sincronização Google Calendar

### Cenários de uso

1. **Importar** eventos do calendário corporativo da FNP → criam `Evento` automaticamente
2. **Exportar** eventos/atividades/missões do sistema para o calendário corporativo
3. **2-way sync**: cada lado é fonte para o outro (mais complexo, último passo)

### Tecnologia: Google Calendar API v3

#### Autenticação

Duas opções:

**A. OAuth 2.0 por usuário** (cada funcionário FNP conecta sua conta)
- Vantagem: vê só os calendários daquele usuário
- Desvantagem: cada um precisa fazer o flow de OAuth no primeiro uso

**B. Service Account** (uma conta de máquina única para toda a FNP)
- Vantagem: setup único; sistema enxerga sempre o mesmo calendário
- Desvantagem: requer Google Workspace (FNP já tem) e
  **domain-wide delegation** habilitado no admin do Workspace
- **Recomendada** para o caso da FNP

#### Setup

```bash
# 1. Google Cloud Console:
#    - Criar projeto "Sistema FNP"
#    - Habilitar Calendar API
#    - Service Account → JSON key
# 2. Workspace Admin:
#    - Security → API controls → Domain-wide delegation
#    - Client ID da SA + scope https://www.googleapis.com/auth/calendar
# 3. Calendário corporativo: compartilhar com a SA (email termina em
#    .iam.gserviceaccount.com)
```

#### Implementação

```bash
pip install google-api-python-client google-auth
```

```python
# aplicacoes/eventos/servicos/google_calendar.py
from google.oauth2 import service_account
from googleapiclient.discovery import build

def _client():
    creds = service_account.Credentials.from_service_account_info(
        settings.GOOGLE_SA_JSON,
        scopes=['https://www.googleapis.com/auth/calendar'],
        subject=settings.GOOGLE_CALENDAR_USER,  # email da conta delegada
    )
    return build('calendar', 'v3', credentials=creds)

def exportar_evento(evento):
    """Cria/atualiza evento no Google Calendar."""
    body = {
        'summary': evento.titulo,
        'description': evento.descricao,
        'start': {'date': evento.data_inicio.isoformat()},
        'end': {'date': (evento.data_fim or evento.data_inicio).isoformat()},
        'location': f'{evento.local} {evento.cidade}',
        'extendedProperties': {
            'private': {'fnp_evento_id': str(evento.pk)},
        },
    }
    cal = _client()
    if evento.google_event_id:
        cal.events().update(calendarId='primary', eventId=evento.google_event_id, body=body).execute()
    else:
        result = cal.events().insert(calendarId='primary', body=body).execute()
        evento.google_event_id = result['id']
        evento.save(update_fields=['google_event_id'])

def importar_eventos(periodo_inicio, periodo_fim):
    """Puxa eventos do Google que não estão no sistema ainda."""
    cal = _client()
    eventos = cal.events().list(
        calendarId='primary',
        timeMin=periodo_inicio.isoformat() + 'Z',
        timeMax=periodo_fim.isoformat() + 'Z',
        singleEvents=True, orderBy='startTime',
    ).execute()
    for ev in eventos.get('items', []):
        fnp_id = ev.get('extendedProperties', {}).get('private', {}).get('fnp_evento_id')
        if fnp_id:
            continue  # ja veio do sistema, pula
        # cria no sistema
        Evento.objects.create(
            titulo=ev['summary'],
            data_inicio=ev['start'].get('date') or ev['start']['dateTime'][:10],
            google_event_id=ev['id'],
            ...
        )
```

#### Mudança no model

```python
class Evento(ModeloBase):
    ...
    google_event_id = models.CharField(max_length=255, blank=True, db_index=True)
```

#### Disparo da sincronização

1. **Push automático** via `post_save` signal — quando criar/editar Evento,
   atualiza no Google
2. **Pull periódico** via `python manage.py sincronizar_google_calendar` rodado
   pelo cron do Render (todo dia 6h da manhã)
3. **Webhook do Google** (Push notifications) para sync em tempo real —
   requer Pub/Sub configurado, mais avançado

#### Custos e limites

- **API gratuita** até 1M requests/dia
- Quota por usuário: 600 req/min — suficiente
- Sem custo financeiro para a FNP

#### Estimativa de implementação

- Setup OAuth/Service Account: 1 dia
- Service `google_calendar.py` + signal: 1 dia
- Comando de sincronização inicial + cron: 0.5 dia
- UI para conectar/desconectar calendar no perfil: 0.5 dia
- Testes: 1 dia
- **Total: ~4 dias** de desenvolvimento

---

## 12. Lacunas exploráveis ainda — oportunidades

1. **Integração com sistemas das prefeituras** — REST API já existe; abrir
   doc em `/api/docs/` (drf-spectacular) e oferecer chave para sistemas de
   prefeituras associadas
2. **App mobile dedicado para recepção** — tablet com webcam dedicado, modo
   kiosk, atalhos físicos
3. **Quiosque de autoatendimento** — visitante encontra QR no balcão →
   abre o pré-credenciamento direto, mesma URL pública
4. **Assinatura digital de documentos** — convênios da FNP com prefeituras
   via integração GovBR ou Clicksign
5. **Dashboards externos** — embedded para imprensa institucional
6. **Newsletter automatizada** — usar `historico_envios` para gerar
   relatório mensal de comunicação enviada
7. **Análise sentimento** de respostas aos e-mails enviados
8. **Recomendação** automática: "Você marcou esse prefeito para o evento X,
   ele costuma faltar — sugerimos avisar com mais antecedência"
9. **Geocoding reverso** — quando importar IBGE, preencher latitude/longitude
   automaticamente
10. **Cache distribuído** (Redis) — quando passar de 1 instância no Render

---

## Plano de ação sugerido — prioridade

### Esta semana
- [ ] Postgres no Render + migração de dados
- [ ] Sentry para captura de erros
- [ ] R2/S3 para mídia + migrar fotos existentes
- [ ] Fix do face-api.js (incluído nesse commit)

### Próximas 2 semanas
- [ ] Hardening dos 5 itens críticos (SECRET_KEY, busca, upload, ModelForm, PII)
- [ ] CI no GitHub Actions rodando os 25 testes
- [ ] Política de privacidade + termo no login
- [ ] Backup script + restore documentado

### Próximo mês
- [ ] Google Calendar sync
- [ ] Departamentos + convite de funcionário
- [ ] Cobertura de testes para 70% (engajamento, adimplência, relatórios)
- [ ] Documentação operacional (runbook)
- [ ] Mobile audit + correções

### Trimestre
- [ ] WhatsApp Cloud API quando passar de 100 msgs/semana
- [ ] Portal externo dos prefeitos completo
- [ ] BI conectado via API REST
- [ ] PWA otimizado

---

## Como avaliar se está pronto

**Pronto para go-live com a equipe:** todos os ✓ checados.

- [ ] Postgres gerenciado em produção
- [ ] Mídia em S3/R2 com CORS configurado
- [ ] Sentry capturando erros
- [ ] Backups automáticos funcionando + restore testado
- [ ] CI rodando no GitHub Actions
- [ ] LGPD: política, termo no login, exportar/excluir dados
- [ ] Permissões granulares por departamento
- [ ] Onboarding dos 80 funcionários: invite por e-mail
- [ ] Pelo menos uma sessão de treinamento gravada
- [ ] Runbook escrito + responsável de plantão definido
