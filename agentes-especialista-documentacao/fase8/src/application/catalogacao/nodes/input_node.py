"""
nodes/input_node.py
--------------------
Segundo nó do grafo (Fase 8) — valida os dados do componente
buscados no atlas_ingestao_api.

Fase 7: validava se a busca do repositório trouxe README/manifesto.
Fase 8: valida se o document_context tem os campos mínimos para
        gerar documentação e catalogação com qualidade.
"""

import logging
from typing import Any

from src.application.state import DocumentacaoState

logger = logging.getLogger(__name__)

# Campos considerados essenciais — sem eles a documentação ficaria
# vazia demais para ter valor
CAMPOS_ESSENCIAIS = ["component_name", "classification", "ownership"]


def input_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Valida o document_context buscado pelo ingestao_fetch_node.

    Args:
        state: Estado atual com document_context preenchido

    Returns:
        dict com atualizações para o estado do grafo
    """
    logger.info("=" * 55)
    logger.info("[input_node] Validando contexto do componente")
    logger.info("=" * 55)

    if state.get("status_final") == "erro":
        logger.warning(
            "[input_node] ⚠ Erro detectado na busca do componente — pulando validação"
        )
        return {"etapa_atual": "input_node"}

    document_context = state.get("document_context")
    erros = list(state.get("erros", []))

    if not document_context:
        erro = "document_context ausente — ingestao_fetch_node pode ter falhado"
        logger.error("[input_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "input_node",
        }

    campos_faltando = [
        campo for campo in CAMPOS_ESSENCIAIS if not document_context.get(campo)
    ]

    if campos_faltando:
        erro = f"Campos essenciais ausentes no document_context: {campos_faltando}"
        logger.warning("[input_node] ⚠ %s", erro)
        erros.append(erro)
        # Não bloqueia o fluxo — segue com aviso, a LLM ainda pode
        # gerar algo útil com o que estiver disponível

    logger.info(
        "[input_node] ✓ Componente: '%s'",
        document_context.get("component_name"),
    )
    logger.info(
        "[input_node] ✓ Tipo: '%s' | Linguagem: '%s'",
        document_context.get("classification", {}).get("application_type"),
        document_context.get("classification", {}).get("main_language"),
    )
    logger.info(
        "[input_node] ✓ Time responsável: '%s'",
        document_context.get("ownership", {}).get("responsible_team"),
    )
    logger.info("[input_node] ✓ Validação concluída — seguindo para documentation_node")

    return {
        "erros": erros,
        "etapa_atual": "input_node",
    }