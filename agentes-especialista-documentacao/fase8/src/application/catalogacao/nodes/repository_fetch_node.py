"""
nodes/repository_fetch_node.py
---------------------------------
Primeiro nó do grafo (Fase 7) — busca o conteúdo do repositório.

Substitui, na ordem do grafo, o papel que o Kafka consumer tinha de
"entregar o JSON pronto". Agora é este nó que traz os dados brutos
a partir de uma URL, antes de qualquer validação ou geração via LLM.

Fluxo:
  1. Recebe repository_url do estado
  2. Chama infrastructure/repository (GitHub mock ou GitLab produção,
     conforme REPOSITORY_PROVIDER no .env)
  3. Preenche repo_data no estado com README, árvore de arquivos,
     manifestos e metadados básicos

Este nó não usa LLM — é busca determinística de dados, mesma natureza
dos nós de persistência (infraestrutura, não geração).
"""

import logging
from typing import Any

from src.application.state import DocumentacaoState
from src.infrastructure.repository import buscar_repositorio

logger = logging.getLogger(__name__)


def repository_fetch_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Busca os dados do repositório a partir da URL informada.

    Args:
        state: Estado atual com repository_url preenchida

    Returns:
        dict com repo_data preenchido, ou erro no estado se a busca falhar
    """
    logger.info("=" * 55)
    logger.info("[repository_fetch_node] Buscando repositório")
    logger.info("=" * 55)

    repository_url = state["repository_url"]
    erros = list(state.get("erros", []))

    logger.info("[repository_fetch_node] URL: %s", repository_url)

    try:
        repo_data = buscar_repositorio(repository_url)

        logger.info(
            "[repository_fetch_node] ✓ Repositório: '%s/%s'",
            repo_data.get("owner"),
            repo_data.get("repo_name"),
        )
        logger.info(
            "[repository_fetch_node] ✓ README: %s",
            "encontrado" if repo_data.get("readme_content") else "não encontrado",
        )
        logger.info(
            "[repository_fetch_node] ✓ Arquivos na árvore: %d",
            len(repo_data.get("arquivos", [])),
        )
        logger.info(
            "[repository_fetch_node] ✓ Manifestos encontrados: %s",
            list(repo_data.get("manifestos", {}).keys()) or "nenhum",
        )
        logger.info(
            "[repository_fetch_node] ✓ Busca concluída — seguindo para input_node"
        )

        return {
            "repo_data": repo_data,
            "erros": erros,
            "etapa_atual": "repository_fetch_node",
        }

    except Exception as exc:
        erro = f"Erro ao buscar repositório '{repository_url}': {str(exc)}"
        logger.error("[repository_fetch_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "repository_fetch_node",
        }