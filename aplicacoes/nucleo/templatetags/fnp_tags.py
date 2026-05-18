"""Template tags customizadas do sistema FNP — avatares e brasões com fallback."""

import hashlib
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()


# Paleta de cores determinísticas para avatares de iniciais — boa legibilidade sobre texto branco.
_PALETA_AVATAR = (
    'bg-rose-500', 'bg-pink-500', 'bg-fuchsia-500', 'bg-purple-500',
    'bg-violet-500', 'bg-indigo-500', 'bg-blue-500', 'bg-sky-500',
    'bg-cyan-500', 'bg-teal-500', 'bg-emerald-500', 'bg-green-500',
    'bg-lime-600', 'bg-yellow-600', 'bg-amber-600', 'bg-orange-500',
    'bg-red-500', 'bg-stone-500', 'bg-zinc-600', 'bg-slate-600',
)


def _hash_nome(nome):
    """Retorna inteiro determinístico a partir do nome para indexar paleta."""
    return int(hashlib.md5(nome.encode()).hexdigest()[:8], 16)


def _iniciais(nome):
    """Extrai até duas iniciais do nome (primeira palavra + última palavra)."""
    partes = [p for p in nome.strip().split() if p]
    if not partes:
        return '?'
    if len(partes) == 1:
        return partes[0][0].upper()
    return (partes[0][0] + partes[-1][0]).upper()


@register.simple_tag
def avatar_pessoa(pessoa, tamanho=150):
    """Retorna URL do avatar da pessoa com fallback para pravatar.cc.

    Args:
        pessoa: Instância de Pessoa.
        tamanho: Dimensão em pixels para o placeholder.

    Returns:
        URL da foto uploadada ou placeholder determinístico baseado no nome.
    """
    if pessoa.foto:
        return pessoa.foto.url
    seed = _hash_nome(pessoa.nome) % 70 + 1
    return f'https://i.pravatar.cc/{tamanho}?img={seed}'


# Mapa de rotulos amigaveis para campos auditados — fallback usa o slug.
_LABELS_CAMPOS = {
    'nome': 'Nome', 'email': 'E-mail', 'telefone': 'Telefone', 'cargo': 'Cargo',
    'partido': 'Partido', 'tipo': 'Tipo', 'genero': 'Gênero', 'foto': 'Foto',
    'biografia_curta': 'Biografia', 'mandato_inicio': 'Início do mandato',
    'mandato_fim': 'Fim do mandato', 'ativo': 'Ativo', 'observacoes': 'Observações',
    'autorizacao_uso_imagem': 'Autorização de imagem',
    'termo_confidencialidade': 'Termo de confidencialidade',
    'uf': 'UF', 'codigo_ibge': 'Código IBGE', 'populacao': 'População',
    'regiao': 'Região', 'brasao': 'Brasão', 'eh_capital': 'É capital?',
    'associado_fnp': 'Associado FNP', 'latitude': 'Latitude', 'longitude': 'Longitude',
    'titulo': 'Título', 'descricao': 'Descrição', 'data_inicio': 'Data de início',
    'data_fim': 'Data de término', 'local': 'Local', 'cidade': 'Cidade',
    'modalidade': 'Modalidade', 'acesso': 'Acesso', 'natureza': 'Natureza',
    'status': 'Status', 'origem': 'Origem', 'forma': 'Forma',
    'categoria': 'Categoria', 'periodicidade_reunioes': 'Periodicidade',
    'ponto_focal_fnp': 'Ponto focal FNP', 'pais': 'País',
    'fonte_recurso': 'Fonte de recurso', 'valor_orcado': 'Valor orçado',
    'data_fim_previsto': 'Término previsto', 'responsavel': 'Responsável',
}


@register.filter
def rotulo_campo(slug):
    """Retorna rótulo humanizado de um campo auditado (ou capitaliza o slug)."""
    if slug in _LABELS_CAMPOS:
        return _LABELS_CAMPOS[slug]
    return slug.replace('_', ' ').capitalize()


@register.simple_tag
def avatar_iniciais(nome_ou_pessoa, classe_tamanho='w-9 h-9', classe_texto='text-sm'):
    """Renderiza HTML de avatar redondo com iniciais e cor determinística.

    Útil para listas grandes onde carregar fotos via HTTP é caro; também
    funciona como fallback offline-friendly do ``avatar_pessoa``.

    Args:
        nome_ou_pessoa: String com o nome ou instância com atributo ``nome``.
        classe_tamanho: Classes Tailwind de dimensão (default w-9 h-9).
        classe_texto: Classes Tailwind do texto interno (default text-sm).

    Returns:
        HTML seguro com o avatar pronto para ser inserido no template.
    """
    nome = getattr(nome_ou_pessoa, 'nome', None) or str(nome_ou_pessoa or '')
    iniciais = _iniciais(nome)
    cor = _PALETA_AVATAR[_hash_nome(nome) % len(_PALETA_AVATAR)]
    html = (
        f'<span class="inline-flex items-center justify-center rounded-full '
        f'{classe_tamanho} {cor} text-white font-semibold {classe_texto} '
        f'select-none flex-shrink-0" title="{nome}">{iniciais}</span>'
    )
    return mark_safe(html)


@register.simple_tag
def brasao_municipio(municipio):
    """Retorna URL do brasão do município com cadeia de fallback.

    Ordem de prioridade: upload do editor > arquivo estático (Wikimedia) > DiceBear.

    Args:
        municipio: Instância de Municipio.

    Returns:
        URL do brasão encontrado na primeira fonte disponível.
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
