"""
infrastructure/repository
----------------------------
Módulo de infraestrutura para busca de repositórios (GitHub/GitLab).

Expõe apenas o necessário para o restante da aplicação:
  - buscar_repositorio: seleciona o provedor e retorna os dados do repositório
"""

import logging

from src.infrastructure.repository.config import get_provider

logger = logging.getLogger(__name__)


def buscar_repositorio(url: str) -> dict:
    """
    Busca as informações de um repositório, escolhendo o provedor
    (GitHub ou GitLab) conforme configurado em REPOSITORY_PROVIDER.

    Args:
        url: URL do repositório

    Returns:
        dict com os dados do repositório (mesmo formato para ambos provedores)
    """
    provider = get_provider()
    logger.info("[repository] Provedor selecionado: '%s'", provider)

    if provider == "github":
        from src.infrastructure.repository.github_client import buscar_repositorio as buscar_github
        return buscar_github(url)

    from src.infrastructure.repository.gitlab_client import buscar_repositorio as buscar_gitlab
    return buscar_gitlab(url)


__all__ = ["buscar_repositorio"]