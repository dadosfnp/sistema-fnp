# Build local do Tailwind CSS

Substitui o CDN runtime (`https://cdn.tailwindcss.com`) por um CSS estático,
gerado durante o build, eliminando: bundle gigante, dependência de CDN externo
em produção e atraso de FOUC no primeiro paint.

## Setup inicial (uma vez)

Requer Node.js 18+ instalado localmente (sem Docker, sem Celery, conforme
convenções do projeto).

```bash
npm install
```

Isso instala apenas `tailwindcss` como devDependency (não há runtime JS).

## Build

```bash
# Build único minificado (para produção / antes do commit)
npm run build:css

# Watch durante o desenvolvimento (regenera ao salvar templates)
npm run watch:css
```

O CSS é gerado em `estaticos/css/tailwind.css` e servido via `{% static %}`.

## Como ativar no `base.html`

Substitua o bloco `<!-- Tailwind CSS -->` em `templates/base.html` por:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/tailwind.css' %}">
```

E remova o `<script>tailwind.config = {...}</script>` (config já em
`tailwind.config.js`). Mantenha `darkMode: 'class'` ali.

## Em produção (Render)

1. Adicionar passo de build no `build.sh` antes do `collectstatic`:
   ```bash
   npm ci && npm run build:css
   python manage.py collectstatic --noinput
   ```
2. Commitar `package-lock.json` para builds reprodutíveis.

## Conteúdo varrido pelo purge

O `tailwind.config.js` aponta para:
- `templates/**/*.html`
- `aplicacoes/**/templates/**/*.html`
- `aplicacoes/**/*.py` (cobre classes em strings dinâmicas tipo `bg-{cor}-50`)

Se alguma classe dinâmica não aparecer em produção, adicionar à `safelist`
no config.
