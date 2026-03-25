import hashlib
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def avatar_pessoa(pessoa, tamanho=150):
    """Retorna URL de foto realista para a pessoa."""
    if pessoa.foto:
        return pessoa.foto.url
    # Gera seed numerico estavel a partir do nome
    seed = int(hashlib.md5(pessoa.nome.encode()).hexdigest()[:8], 16) % 70 + 1
    return f'https://i.pravatar.cc/{tamanho}?img={seed}'


@register.simple_tag
def brasao_municipio(municipio):
    """Retorna URL do brasao real do municipio (local ou fallback)."""
    brasoes_dir = Path(settings.BASE_DIR) / 'estaticos' / 'img' / 'brasoes'
    # Tenta SVG primeiro, depois PNG
    for ext in ('svg', 'png'):
        arquivo = brasoes_dir / f'{municipio.codigo_ibge}.{ext}'
        if arquivo.exists():
            return static(f'img/brasoes/{municipio.codigo_ibge}.{ext}')
    # Fallback: DiceBear shapes
    return f'https://api.dicebear.com/9.x/shapes/svg?seed={municipio.nome}&backgroundColor=059669,0284c7,7c3aed,d97706,dc2626'
