"""
infrastructure/ingestao_api
------------------------------
Módulo de infraestrutura para leitura do MongoDB do atlas-apis-ingestao.

Expõe apenas o necessário para o restante da aplicação:
  - get_ingestao_database: context manager de conexão (somente leitura)
  - DocumentContextRepository: busca de componentes por component_name
"""

from src.infrastructure.ingestao_api.client import get_ingestao_database
from src.infrastructure.ingestao_api.repositories import DocumentContextRepository

__all__ = [
    "get_ingestao_database",
    "DocumentContextRepository",
]