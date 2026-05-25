"""Validadores de arquivos com checagens reais — não confia em extensão ou MIME do browser.

Hardening LGPD/segurança: uploads são vetor crítico de XSS, RCE e DoS.
Aqui validamos magic bytes + Pillow para imagens, e tamanho para qualquer
arquivo. Aplicar em FileField/ImageField via ``validators=[...]``.
"""

from django.core.exceptions import ValidationError

# Limites globais — ajustáveis via settings se necessário.
TAMANHO_MAX_IMAGEM_MB = 10
TAMANHO_MAX_ANEXO_MB = 25


def _bytes_iniciais(arquivo, n=32):
    """Lê os primeiros bytes preservando o cursor original."""
    pos = arquivo.tell()
    try:
        arquivo.seek(0)
        return arquivo.read(n)
    finally:
        arquivo.seek(pos)


def validar_imagem_segura(arquivo):
    """Valida que ``arquivo`` é realmente JPG, PNG ou WebP.

    Bloqueia:
    - Extensões falsas (``foto.png`` que é HTML/SVG malicioso)
    - Arquivos corrompidos que poderiam explorar libs de imagem
    - Imagens maiores que ``TAMANHO_MAX_IMAGEM_MB`` (DoS por memória)

    Raises:
        ValidationError: com mensagem clara para o usuário.
    """
    # 1. Limite de tamanho — antes de tudo, evita ler GB em memória
    tamanho = getattr(arquivo, 'size', None)
    if tamanho is not None and tamanho > TAMANHO_MAX_IMAGEM_MB * 1024 * 1024:
        raise ValidationError(
            f'Imagem maior que {TAMANHO_MAX_IMAGEM_MB} MB. '
            f'Reduza o tamanho antes de enviar.'
        )

    # 2. Magic bytes — checa assinatura binária real
    cabecalho = _bytes_iniciais(arquivo, 32)
    eh_jpeg = cabecalho.startswith(b'\xff\xd8\xff')
    eh_png = cabecalho.startswith(b'\x89PNG\r\n\x1a\n')
    eh_webp = cabecalho[:4] == b'RIFF' and cabecalho[8:12] == b'WEBP'
    if not (eh_jpeg or eh_png or eh_webp):
        raise ValidationError(
            'Apenas imagens JPG, PNG ou WebP são aceitas. '
            'Envie um arquivo de imagem válido.'
        )

    # 3. Pillow.verify — detecta corrupção e arquivos manipulados
    try:
        from PIL import Image, UnidentifiedImageError
        pos = arquivo.tell()
        arquivo.seek(0)
        img = Image.open(arquivo)
        img.verify()
        arquivo.seek(pos)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as exc:
        raise ValidationError(
            f'Arquivo de imagem corrompido ou inválido: {exc}'
        ) from exc


def validar_anexo_seguro(arquivo):
    """Valida anexos genéricos (PDF, DOCX, XLSX, imagens, etc).

    Bloqueia executáveis e tipos perigosos por extensão + tamanho máximo.
    Não valida conteúdo profundo — assume que o anexo é um documento de
    trabalho. Para anexos de e-mail.
    """
    tamanho = getattr(arquivo, 'size', None)
    if tamanho is not None and tamanho > TAMANHO_MAX_ANEXO_MB * 1024 * 1024:
        raise ValidationError(
            f'Anexo maior que {TAMANHO_MAX_ANEXO_MB} MB.'
        )

    nome = (getattr(arquivo, 'name', '') or '').lower()
    extensoes_bloqueadas = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.msi',
        '.vbs', '.vbe', '.js', '.jse', '.wsf', '.wsh',
        '.ps1', '.psm1', '.app', '.dmg', '.jar', '.sh',
    }
    for ext in extensoes_bloqueadas:
        if nome.endswith(ext):
            raise ValidationError(
                f'Anexos do tipo {ext} não são aceitos por motivos de segurança.'
            )


def mascarar_pii(texto):
    """Remove/mascara CPF, telefone e e-mail de uma string.

    Usado em LogAlteracao.objeto_repr e em qualquer lugar onde texto livre
    possa virar log persistente. Preserva tudo o resto.
    """
    import re

    if not texto:
        return texto

    # CPF: XXX.XXX.XXX-XX ou apenas 11 dígitos
    texto = re.sub(r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', '***.***.***-**', texto)
    texto = re.sub(r'\b\d{11}\b', lambda m: m.group(0)[:3] + '*' * 6 + m.group(0)[-2:], texto)
    # E-mail
    texto = re.sub(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b',
                   lambda m: m.group(0).split('@')[0][:2] + '***@' + m.group(0).split('@')[1],
                   texto)
    # Telefone BR — (XX) XXXXX-XXXX ou variações
    texto = re.sub(r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
                   lambda m: m.group(0)[:4] + '****' + m.group(0)[-2:], texto)
    return texto
