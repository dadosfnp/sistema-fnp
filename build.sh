#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Cria superuser inicial se as variaveis estiverem definidas e ele ainda nao existir.
# DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py createsuperuser --no-input || true
fi

# Seeds idempotentes — todos usam update_or_create, seguro rodar a cada deploy.
# Dicionario institucional (~53 termos), pesos do engajamento (10 chaves)
# e municipios mockup (~57 cidades com lat/lng + adimplencia) para o mapa.
python manage.py popular_dicionario || true
python manage.py popular_pesos_engajamento || true
python manage.py popular_mapa_brasil || true
