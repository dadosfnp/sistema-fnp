# Deploy automático — GitHub Actions → Digital Ocean

Workflow em `.github/workflows/deploy.yml`. Dispara a cada push para `master`
e executa via SSH no droplet:

1. `cd /var/www/fnp/sistema-fnp`
2. Carrega variáveis do `.env` no shell
3. `git pull origin master`
4. Ativa o venv (`venv/bin/activate`)
5. `pip install -r requirements.txt`
6. `python manage.py migrate --noinput`
7. `python manage.py collectstatic --noinput --clear`
8. `systemctl restart fnp`

## Secrets a configurar no GitHub

**Repositório → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Valor |
|---|---|
| `DO_HOST` | IP do droplet, ex: `142.93.205.222` (ou hostname quando tiver DNS) |
| `DO_USER` | `root` (atual) ou um usuário dedicado com permissão de `systemctl restart fnp` |
| `DO_SSH_KEY` | Chave privada SSH completa (inclui as linhas `-----BEGIN OPENSSH PRIVATE KEY-----` e `-----END...`) |

## Gerar par SSH dedicado para o GitHub

No droplet:

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/github_deploy -C "github-actions"

# Adicionar a publica em authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Imprimir a privada para copiar no secret DO_SSH_KEY
cat ~/.ssh/github_deploy
```

Copie **tudo** que aparece (linhas BEGIN/END incluídas) e cole no secret `DO_SSH_KEY` no GitHub.

## Testar o deploy

1. Cadastre os 3 secrets acima no GitHub
2. Faça um commit qualquer (ex: editar este arquivo) e `git push origin master`
3. Acompanhe em **GitHub → seu repo → Actions → Deploy Sistema FNP**
4. O job leva ~1-2 min. No final, confira no droplet:
   ```bash
   systemctl status fnp
   ```
   Deve estar `active (running)`.

## Troubleshooting

| Sintoma | Causa provável | Como resolver |
|---|---|---|
| `Permission denied (publickey)` | Chave SSH errada ou não autorizada | Re-gerar par e copiar a privada inteira no secret |
| `Host key verification failed` | Primeira conexão ao IP | Adicionar `script_stop: false` e refazer (raramente acontece com appleboy) |
| `sudo: a password is required` | Usuário não é root e não tem NOPASSWD | Usar `root` em `DO_USER`, ou criar `/etc/sudoers.d/fnp-deploy` |
| `migrate` falha | Falta `DATABASE_URL` no `.env` | `cat .env \| grep DATABASE_URL` no droplet |
| `collectstatic` falha | Permissão em `staticfiles/` | `chown -R $USER:www-data /var/www/fnp/sistema-fnp/staticfiles` |
| Serviço não reinicia | Erro de import após `git pull` | `journalctl -u fnp -n 50` para ver o stack |

## Rollback rápido

Se um deploy quebrar produção:

```bash
# No droplet:
cd /var/www/fnp/sistema-fnp
git log --oneline -5            # ache o commit bom
git reset --hard <hash-bom>
systemctl restart fnp
```

E **reverter também no GitHub** para a próxima rodada não regredir:
```bash
# Localmente:
git revert <hash-ruim>
git push origin master   # dispara novo deploy ja com o revert aplicado
```
