# Deploy automático — GitHub Actions → Digital Ocean

Workflow em `.github/workflows/deploy.yml`. Dispara em push para `master`
(ou manualmente em **Actions → Deploy Sistema FNP → Run workflow**) e:

1. Roda a suíte de testes contra um PostgreSQL 16 efêmero
2. Se passar, faz SSH no droplet, `git pull`, atualiza dependências,
   `migrate`, `collectstatic` e reinicia o `fnp.service`

## Secrets a configurar (GitHub → Settings → Secrets and variables → Actions)

| Secret | Obrigatório | Exemplo / valor |
|---|---|---|
| `DEPLOY_HOST` | ✅ | `203.0.113.45` ou `sistema.fnp.org.br` |
| `DEPLOY_USER` | ✅ | `fnp` (recomendado — usuário dedicado, sem sudo geral) |
| `DEPLOY_SSH_KEY` | ✅ | Conteúdo da chave privada (`cat ~/.ssh/id_ed25519`) — gerar par dedicado para o GitHub e adicionar a pública no `~/.ssh/authorized_keys` do droplet |
| `DEPLOY_PATH` | ✅ | `/opt/sistema-fnp` (ou onde o `git clone` foi feito) |
| `DEPLOY_PORT` | opcional | `22` (default) |
| `DEPLOY_VENV_PATH` | opcional | `.venv` (default — caminho do venv relativo ao DEPLOY_PATH) |
| `DEPLOY_SERVICE` | opcional | `fnp.service` (default) |

## Pré-requisitos no droplet

1. Usuário `fnp` (ou o que estiver em `DEPLOY_USER`) tem permissão de:
   - Escrever em `DEPLOY_PATH`
   - Rodar `sudo systemctl restart fnp.service` **sem senha**
2. Configurar sudoers para esse comando específico:
   ```bash
   echo 'fnp ALL=(ALL) NOPASSWD: /bin/systemctl restart fnp.service, /bin/systemctl is-active fnp.service' \
     | sudo tee /etc/sudoers.d/fnp-deploy
   sudo chmod 440 /etc/sudoers.d/fnp-deploy
   ```
3. Repositório já clonado em `DEPLOY_PATH` com `git remote` apontando para o GitHub
4. Virtualenv criado em `DEPLOY_PATH/.venv` com Python 3.12

## Gerar chave SSH dedicada para o GitHub

No droplet (como root ou via sudo):

```bash
# Como o usuário fnp:
sudo -u fnp ssh-keygen -t ed25519 -N "" -f /home/fnp/.ssh/github_deploy
# Adicionar a publica em authorized_keys
sudo -u fnp bash -c 'cat /home/fnp/.ssh/github_deploy.pub >> /home/fnp/.ssh/authorized_keys'
# Mostrar a privada para copiar no secret DEPLOY_SSH_KEY
sudo cat /home/fnp/.ssh/github_deploy
```

Copie o conteúdo COMPLETO (incluindo as linhas `-----BEGIN OPENSSH PRIVATE KEY-----`
e `-----END OPENSSH PRIVATE KEY-----`) e cole no secret `DEPLOY_SSH_KEY`.

## Testando o deploy

1. Faça um commit cosmético (ex: editar `README.md`) e push para `master`
2. Acompanhe em **Actions → Deploy Sistema FNP**
3. O job `testes` deve passar primeiro; em seguida `deploy` faz SSH
4. Confira no droplet: `sudo systemctl status fnp.service` deve estar `active`

Em caso de falha:
- Job de testes vermelho → fix nos testes, commit, push
- Job de deploy vermelho com "Permission denied (publickey)" → revisar chave SSH
- "sudo: a password is required" → faltou o sudoers do passo 2
- Serviço não ativa após restart → conferir `journalctl -u fnp.service -n 50` no droplet

## Rollback

Se uma versão quebrar em produção:

```bash
# No droplet:
cd /opt/sistema-fnp
git log --oneline -5            # identifica o commit bom
git reset --hard <hash-bom>
sudo systemctl restart fnp.service
```

Para evitar repetir o erro, **reverter no GitHub também**:
```bash
git revert <hash-ruim>
git push origin master  # dispara novo deploy com o revert
```
