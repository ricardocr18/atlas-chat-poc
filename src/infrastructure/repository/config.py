"""
infrastructure/repository/config.py
--------------------------------------
Configurações e seleção do provedor de repositório (GitHub ou GitLab).

Fase 7: o agente passa a buscar informações de um repositório de código
via API REST, em vez de receber um JSON pronto via Kafka.

Dois provedores suportados:
  github  → mock local (repositórios públicos, sem autenticação obrigatória)
  gitlab  → produção Sicredi (repositórios privados, exige token)

A seleção é controlada por REPOSITORY_PROVIDER no .env — mesmo padrão
usado no INPUT_MODE do Kafka (Fase 4): uma variável de ambiente muda
o comportamento sem tocar em código.
"""

import logging

from src.settings import get_settings

logger = logging.getLogger(__name__)


def get_provider() -> str:
    """
    Retorna o provedor de repositório configurado.

    Returns:
        "github" ou "gitlab"
    """
    settings = get_settings()
    provider = settings.repository_provider.lower()

    if provider not in ("github", "gitlab"):
        raise ValueError(
            f"REPOSITORY_PROVIDER='{provider}' inválido. "
            "Use 'github' ou 'gitlab'."
        )

    return provider


def montar_headers_github() -> dict[str, str]:
    """
    Monta os headers da requisição para a API do GitHub.

    Sem token: limite de 60 requisições/hora (suficiente para o mock).
    Com token: limite sobe para 5.000 requisições/hora.
    """
    settings = get_settings()
    headers = {"Accept": "application/vnd.github+json"}

    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
        logger.debug("Requisição GitHub autenticada com token.")
    else:
        logger.debug("Requisição GitHub sem token — limite de 60 req/hora.")

    return headers


def montar_headers_gitlab() -> dict[str, str]:
    """
    Monta os headers da requisição para a API do GitLab.

    Preencher GITLAB_TOKEN quando tiver acesso ao GitLab da Sicredi.
    Sem token, requisições a repositórios privados falharão com 401/404.
    """
    settings = get_settings()
    headers = {}

    if settings.gitlab_token:
        headers["PRIVATE-TOKEN"] = settings.gitlab_token
        logger.debug("Requisição GitLab autenticada com token.")
    else:
        logger.warning(
            "GITLAB_TOKEN não configurado — repositórios privados "
            "da Sicredi não poderão ser acessados."
        )

    return headers