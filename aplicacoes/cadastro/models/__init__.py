"""Pacote de models do cadastro — re-exporta para preservar imports legados.

Imports como ``from aplicacoes.cadastro.models import Pessoa`` continuam
funcionando. Cada entidade vive em seu próprio submódulo para reduzir
arquivos grandes.
"""

from .municipio import Municipio
from .pauta import EnvolvimentoPauta, Pauta
from .pessoa import Pessoa
from .vinculo import VinculoMunicipio

__all__ = ['Municipio', 'Pessoa', 'Pauta', 'EnvolvimentoPauta', 'VinculoMunicipio']
