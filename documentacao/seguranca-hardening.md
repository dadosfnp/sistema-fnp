# Plano de hardening de segurança — Sistema FNP

> **Quando aplicar:** depois que o front estiver fechado e o Postgres em nuvem
> estiver pronto para receber dados reais (CPFs, telefones, e-mails de prefeitos
> e secretários). Hoje o sistema roda só com mockups locais.

## Status: AGUARDANDO

- [ ] Postgres em nuvem provisionado
- [ ] Front-end fechado (sem features novas grandes pendentes)
- [ ] Plano abaixo executado em ordem

---

## 🔴 Crítico (1–5)

### 1. `SECRET_KEY` fail-fast quando ausente
**Onde:** [configuracao/base.py:14](../configuracao/base.py)
**Atual:** `SECRET_KEY = os.environ.get('SECRET_KEY', 'chave-insegura-troque-em-producao')`
**Fix:**
```python
SECRET_KEY = os.environ['SECRET_KEY']  # KeyError fatal se faltar — proposital
```
Em `producao.py`, validar tamanho mínimo (50 chars).

### 2. Endpoint `/api/busca/` filtra por perfil
**Onde:** [aplicacoes/nucleo/views.py](../aplicacoes/nucleo/views.py) `busca_global`
**Risco:** Visualizador vê qualquer pessoa do Brasil.
**Fix:** Aceitar query e cruzar com `request.user.perfil.municipio_vinculado` ou
permissões granulares para limitar o scope. Visualizador sem município vinculado
só vê instâncias/eventos públicos, nunca pessoas.

### 3. Upload de imagem com validação real
**Onde:** `Pessoa.foto`, `Municipio.brasao`, anexos de comunicação.
**Risco:** `.svg` ou `.html` mascarado de `.png` roda XSS no `<img>`.
**Fix:**
```python
from PIL import Image
import magic

def validar_imagem(f):
    mime = magic.from_buffer(f.read(2048), mime=True)
    if mime not in {'image/jpeg', 'image/png', 'image/webp'}:
        raise ValidationError('Apenas JPG, PNG, WebP.')
    f.seek(0)
    Image.open(f).verify()  # detecta arquivo corrompido
    f.seek(0)
```
Aplicar em `validators=[validar_imagem]` nos ImageField.

### 4. CSRF token global removido de base.html
**Onde:** [templates/base.html](../templates/base.html) — `<span style="display:none">{% csrf_token %}</span>`
**Risco:** Token vaza no HTML; embora helper leia do cookie, o input continua presente.
**Fix:** Decorar `inicio` view com `@ensure_csrf_cookie` e remover o span global.
Cookie continua acessível para `window.csrftoken()`.

### 5. ModelForm com `fields` explícito (sem `__all__`)
**Onde:** Todos os ModelForm em `aplicacoes/*/forms.py`
**Risco:** Mass assignment — POST com `is_staff=true` no body promove usuário.
**Fix:** Audit cada `Meta` e listar campos um a um. Negar campos administrativos.

---

## 🟠 Alto (6–10)

### 6. Postgres em produção
**Onde:** [configuracao/producao.py](../configuracao/producao.py)
**Fix:** Render PG free tier (1 GB suficiente para 5.570 municípios + dados).
`dj-database-url` já configurado. Apenas ativar o add-on.

### 7. Validar `DEBUG=False` em runtime
**Fix:** Em `producao.py`, ao final:
```python
assert not DEBUG, 'DEBUG não pode estar True em produção'
```

### 8. Rate limit em mala direta
**Onde:** [aplicacoes/comunicacao/views.py](../aplicacoes/comunicacao/views.py) `processar_envio`
**Fix:** `django-ratelimit` + cap manual de 200 destinatários por envio + confirmação
quando > 50.

### 9. Mascarar PII em `LogAlteracao.objeto_repr`
**Onde:** [aplicacoes/nucleo/servicos/auditoria.py](../aplicacoes/nucleo/servicos/auditoria.py)
**Fix:** Helper `_repr_seguro(obj)` que substitui CPF/email/telefone por hash ou
"***" antes de salvar. Audit log continua útil sem expor PII.

### 10. Validador de slugs em `Perfil.permissoes_extras`
**Onde:** [aplicacoes/nucleo/models.py](../aplicacoes/nucleo/models.py)
**Fix:**
```python
def clean(self):
    slugs_validos = {s for s, _ in self.PERMISSOES_DISPONIVEIS}
    invalidos = set(self.permissoes_extras or []) - slugs_validos
    if invalidos:
        raise ValidationError(f'Permissões inválidas: {invalidos}')
```

---

## 🟡 Médio (11–16)

### 11. Senhas de mockup vetadas em produção
**Onde:** `popular_mockup` management command.
**Fix:** Abortar com `raise CommandError` se `not settings.DEBUG`.

### 12. JWT com expiração
**Onde:** `obtain_auth_token` em [configuracao/urls.py](../configuracao/urls.py)
**Fix:** Trocar `rest_framework.authtoken` por `djangorestframework-simplejwt`.
Token de acesso curto (15 min) + refresh (7 dias).

### 13. URL do portal_prefeito reorganizada
**Onde:** [configuracao/urls.py](../configuracao/urls.py)
**Fix:** Mover `portal_prefeito` para `aplicacoes/nucleo/urls.py` como URL nomeada
normal. Remover gambiarra `__import__`.

### 14. CSP via django-csp
**Onde:** [configuracao/producao.py](../configuracao/producao.py)
**Fix:**
```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", 'cdn.tailwindcss.com', 'unpkg.com', 'cdn.jsdelivr.net', "'unsafe-inline'")
CSP_STYLE_SRC = ("'self'", 'fonts.googleapis.com', 'unpkg.com', "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", 'data:', 'i.pravatar.cc', 'api.dicebear.com', '*.basemaps.cartocdn.com')
CSP_FONT_SRC = ("'self'", 'fonts.gstatic.com')
CSP_CONNECT_SRC = ("'self'", 'raw.githubusercontent.com')
```
Tirar `'unsafe-inline'` quando substituir Alpine.js inline por SFC bundles.

### 15. CORS controlado
**Fix:** `django-cors-headers` com allowlist de domínios que podem consumir a API
(PowerBI da FNP, sistemas de prefeituras associadas).

### 16. Purga real de soft-deletados
**Fix:** Comando `python manage.py purgar_arquivados --antes=YYYY-MM-DD` que
hard-deleta registros antigos com nota no LogAlteracao. Necessário para LGPD
(direito ao esquecimento).

---

## Checklist de "go-live" (LGPD)

- [ ] Política de privacidade publicada e linkada no rodapé
- [ ] Termo de uso aceito no primeiro login
- [ ] Endpoint `/conta/exportar-meus-dados/` (Art. 18 LGPD)
- [ ] Endpoint `/conta/solicitar-exclusao/` (workflow de aprovação)
- [ ] DPO identificado no projeto e no app
- [ ] Logs de acesso com retenção definida (sugestão: 12 meses)
- [ ] Backup criptografado, RPO/RTO documentados
- [ ] Procedimento de incidente (quem chama, em quanto tempo)

## Ordem sugerida de execução

1. Postgres em prod + backup automático ➜ ganha durabilidade
2. SECRET_KEY fail-fast + DEBUG=False assert ➜ blinda secrets
3. ModelForm.fields + validação de upload ➜ blinda input
4. Mascaramento PII em audit + purge soft-delete ➜ LGPD
5. CSP + CORS ➜ blinda runtime browser
6. JWT + rate limit ➜ blinda API
7. Permissões granulares com validação ➜ blinda autorização
