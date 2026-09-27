"""
nodes/ingestao_fetch_node.py
--------------------------------
Primeiro nó do grafo (Fase 8) — busca o contexto do componente no
MongoDB do atlas-apis-ingestao.

Substitui, na ordem do grafo, o repository_fetch_node da Fase 7.
Em vez de buscar README/manifesto via API do GitHub/GitLab, busca
o documento já normalizado e estruturado pelo atlas-apis-ingestao.

Este nó não usa LLM — é busca determinística de dados, mesma natureza
dos nós de persistência (infraestrutura, não geração).

Descoberta manual (Fase 8): o component_name vem fixo do .env. Um
mecanismo automático (polling periódico no MongoDB, ou consumo de
evento Kafka publicado pelo atlas-apis-ingestao) fica para uma fase
futura, quando o volume ou a necessidade justificar a automação.
"""

import logging
from typing import Any

from src.application.state import DocumentacaoState
from src.infrastructure.ingestao_api import (
    DocumentContextRepository,
    get_ingestao_database,
)

logger = logging.getLogger(__name__)


def ingestao_fetch_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Busca o document_context do componente no MongoDB de ingestão.

    Args:
        state: Estado atual com component_name preenchido

    Returns:
        dict com document_context preenchido, ou erro no estado se
        o componente não for encontrado ou a conexão falhar
    """
    logger.info("=" * 55)
    logger.info("[ingestao_fetch_node] Buscando contexto do componente")
    logger.info("=" * 55)

    component_name = state["component_name"]
    erros = list(state.get("erros", []))

    logger.info("[ingestao_fetch_node] component_name: '%s'", component_name)

    try:
        with get_ingestao_database() as db:
            repo = DocumentContextRepository(db)
            document_context = repo.buscar_por_component_name(component_name)

        if not document_context:
            erro = (
                f"Componente '{component_name}' não encontrado em "
                f"atlas_ingestao_api.document_context"
            )
            logger.error("[ingestao_fetch_node] ✗ %s", erro)
            erros.append(erro)
            return {
                "erros": erros,
                "status_final": "erro",
                "etapa_atual": "ingestao_fetch_node",
            }

        logger.info(
            "[ingestao_fetch_node] ✓ Componente encontrado: '%s'",
            document_context.get("component_name"),
        )
        logger.info(
            "[ingestao_fetch_node] ✓ Categoria: '%s' | Status: '%s'",
            document_context.get("classification", {}).get("application_type"),
            document_context.get("status"),
        )
        logger.info(
            "[ingestao_fetch_node] ✓ Criticidade: '%s'",
            document_context.get("quality", {}).get("criticality"),
        )
        logger.info(
            "[ingestao_fetch_node] ✓ Busca concluída — seguindo para input_node"
        )

        return {
            "document_context": document_context,
            "erros": erros,
            "etapa_atual": "ingestao_fetch_node",
        }

    except Exception as exc:
        erro = f"Erro ao buscar componente '{component_name}': {str(exc)}"
        logger.error("[ingestao_fetch_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "ingestao_fetch_node",
        }