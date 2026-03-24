# Sistema FNP

> Plataforma unificada de gestão institucional da Frente Nacional de Prefeitos.

## Sobre

Sistema web para centralizar o cadastro de pessoas (equipe interna, prefeitos, secretários, assessores), municípios associados, controle de adimplência, acompanhamento de engajamento e gestão de eventos da FNP.

## Stack

- **Backend:** Django 5.x + Python 3.12
- **Banco de dados:** PostgreSQL 16
- **Frontend:** Django Templates + HTMX + Tailwind CSS + Alpine.js
- **Admin:** Django Unfold

## Configuração local

### Pré-requisitos

- Python 3.12+
- PostgreSQL 16+ (instalado e rodando)
- Git

### Passos

```bash
# 1. Clonar o repositório
git clone https://github.com/fnp/sistema-fnp.git
cd sistema-fnp

# 2. Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# 3. Instalar dependências
pip install -r requisitos/local.txt

# 4. Criar banco de dados
createdb sistema_fnp

# 5. Configurar variáveis de ambiente
cp .env.exemplo .env
# Editar .env com seus dados locais (senha do PostgreSQL, etc)

# 6. Rodar migrações
python manage.py migrate

# 7. Criar superusuário
python manage.py createsuperuser

# 8. Rodar o servidor
python manage.py runserver
```

Acesse `http://localhost:8000` para o sistema e `http://localhost:8000/admin/` para o painel administrativo.

## Documentação

- [Arquitetura do sistema](documentacao/arquitetura/LEIAME.md)
- [Decisões arquiteturais (RDAs)](documentacao/arquitetura/decisoes/)

## Licença

Uso interno — Frente Nacional de Prefeitos.
