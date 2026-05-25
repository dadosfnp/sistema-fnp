# Setup de autenticação — Sistema FNP

Sistema FNP usa **django-allauth (Google OAuth) + login local + 2FA TOTP + django-axes**.
Este guia mostra como configurar do zero numa máquina nova ou no Render.

---

## 1. Variáveis de ambiente

Copie `.env.exemplo` para `.env` e preencha:

```
SECRET_KEY=...                          # 50+ caracteres aleatórios
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
DATABASE_URL=postgresql://...           # produção (Digital Ocean)
```

## 2. Criar credencial Google OAuth

1. Acesse https://console.cloud.google.com/
2. Selecione (ou crie) o projeto da FNP
3. Menu lateral: **APIs & Services → Credentials**
4. Clique em **+ Create credentials → OAuth client ID**
5. Tipo: **Web application**
6. Nome: `Sistema FNP`
7. **Authorized JavaScript origins**:
   - `http://localhost:8000` (dev)
   - `https://sistemafnp.onrender.com` (prod — ajuste para seu domínio)
8. **Authorized redirect URIs**:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `https://sistemafnp.onrender.com/accounts/google/login/callback/`
9. Salve e copie **Client ID** + **Client Secret** para o `.env`

## 3. Aplicar configuração no banco

```bash
python manage.py migrate
python manage.py configurar_google_oauth
```

O segundo comando cria o `SocialApp` Google na tabela do allauth com os valores do `.env`. Idempotente — pode rodar de novo após trocar credencial.

## 4. Testar login

1. `python manage.py runserver`
2. Abra http://localhost:8000/accounts/google/login/
3. Faça login com uma conta `@fnp.org.br` → deve cair direto no dashboard
4. Faça logout e tente com conta externa (Gmail pessoal) → deve cair em **"Aguardando aprovação"**

## 5. Aprovar um externo

1. Acesse `/admin/` como superuser
2. Menu **Núcleo → Perfis**
3. Filtre por **Status de aprovação: Pendente**
4. Abra o perfil, ajuste:
   - **Tipo:** `Externo` (ou `Prefeito` se for portal)
   - **Municípios visíveis:** lista do que pode ver
   - **Permissões extras:** marcadores granulares
   - **Expira em:** data limite (default 90 dias)
   - **Justificativa do acesso:** por que precisa
5. Use a ação **"Aprovar acesso dos perfis selecionados"**

Para conceder acesso a entidades específicas (Evento X, Missão Y), use o admin **Núcleo → Permissões por entidade** (ACL por objeto).

## 6. 2FA TOTP (perfis externos e admins)

Externos têm `requer_2fa=True` por padrão. Ao logar pela primeira vez após aprovação, o usuário é redirecionado para `/conta/2fa/setup/` para escanear o QR code com Google Authenticator (ou similar). Recebe 8 códigos de backup — orientar a guardá-los.

Se o usuário perder o celular **e** os códigos, o admin pode resetar acessando `/admin/django_otp/` e deletando o `TOTPDevice` daquele usuário. Ele cairá no setup de novo no próximo login.

## 7. Bloqueio de brute-force (django-axes)

- 5 tentativas falhas no mesmo IP/usuário → bloqueio por **1 hora**
- Sucesso reseta o contador
- Para desbloquear manualmente: `/admin/axes/accessattempt/` e delete os registros

## 8. Auditoria LGPD

- `/admin/nucleo/logacessosensivel/` — quem viu detalhe de Pessoa/Visita/CredPrévio
- `/admin/nucleo/logalteracao/` — quem alterou o quê
- `/admin/nucleo/aceitetermo/` — quem aceitou o termo e quando
- `/admin/nucleo/solicitacaoexclusao/` — pedidos LGPD Art. 18 VI

## 9. Purgar dados antigos (LGPD Art. 16)

```bash
# Simular sem alterar
python manage.py purgar_dados_antigos --dry-run

# Apenas anonimizar Visitas >5 anos (sem deletar nada)
python manage.py purgar_dados_antigos --so-anonimizar

# Executar política completa
python manage.py purgar_dados_antigos
```

Recomendado: agendar via cron do Render (`render.yaml`) para rodar mensalmente.

## 10. Troubleshooting

| Problema | Solução |
|---|---|
| "OAuth not configured" | Rodar `configurar_google_oauth` após popular `.env` |
| Redirect URI mismatch | Conferir se a URI está exata no Google Console (com barra final) |
| "Account inactive" no Google | A conta Workspace está suspensa pelo admin do Google |
| Externo aparovado não vê nada | Faltou adicionar municípios em `municipios_visiveis` ou criar `PermissaoEntidade` |
| 2FA não aceita o código | Verificar relógio do servidor (TOTP exige hora correta ± 30s) |
