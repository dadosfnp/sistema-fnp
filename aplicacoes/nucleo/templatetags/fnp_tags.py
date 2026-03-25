import hashlib
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def avatar_pessoa(pessoa, tamanho=150):
    """Retorna URL de foto da pessoa.

    Prioridade: foto uploaded > placeholder pravatar.
    """
    if pessoa.foto:
        return pessoa.foto.url
    seed = int(hashlib.md5(pessoa.nome.encode()).hexdigest()[:8], 16) % 70 + 1
    return f'https://i.pravatar.cc/{tamanho}?img={seed}'


@register.simple_tag
def brasao_municipio(municipio):
    """Retorna URL do brasao do municipio.

    Prioridade: brasao uploaded > arquivo estatico > fallback DiceBear.
    """
    # 1. Campo brasao do model (upload pelo editor)
    if municipio.brasao:
        return municipio.brasao.url

    # 2. Arquivo estatico baixado do Wikimedia
    brasoes_dir = Path(settings.BASE_DIR) / 'estaticos' / 'img' / 'brasoes'
    for ext in ('svg', 'png'):
        arquivo = brasoes_dir / f'{municipio.codigo_ibge}.{ext}'
        if arquivo.exists():
            return static(f'img/brasoes/{municipio.codigo_ibge}.{ext}')

    # 3. Fallback
    return f'https://api.dicebear.com/9.x/shapes/svg?seed={municipio.nome}&backgroundColor=059669,0284c7,7c3aed,d97706,dc2626'
