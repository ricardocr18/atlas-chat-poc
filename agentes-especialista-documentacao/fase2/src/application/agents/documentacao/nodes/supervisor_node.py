"""
nodes/supervisor_node.py
--------------------------
Último nó do grafo — valida e consolida o resultado final.

Responsabilidade: verificar se todos os nós anteriores executaram
com sucesso, consolidar o estado final e emitir o log de conclusão.

O supervisor_node é o "controle de qualidade" do grafo:
  - Verifica se as duas collections foram populadas
  - Verifica se não houve erros acumulados
  - Define o status_final: "sucesso" ou "erro_parcial"
  - Emite um resumo completo da execução

Futuro (Fase 6): o supervisor poderá notificar o agente de
classificação (atlas-agente-especialista-classificacao) que
um novo componente foi documentado e está pronto para curadoria.
"""

import logging
from typing import Any

from src.application.agents.documentacao.state import DocumentacaoState

logger = logging.getLogger(__name__)


def supervisor_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Valida o resultado final e consolida o estado do grafo.

    Verifica:
      - IDs do MongoDB foram gerados (persistência ok)
      - Não há erros acumulados no estado
      - Todos os dados esperados estão presentes

    Args:
        state: Estado completo após todos os nós anteriores

    Returns:
        dict com status_final e etapa_atual atualizados
    """
    logger.info("=" * 55)
    logger.info("[supervisor_node] Validando resultado final do grafo")
    logger.info("=" * 55)

    erros = list(state.get("erros", []))
    id_previa = state.get("id_mongodb_previa")
    id_metadados = state.get("id_mongodb_metadados")
    previa = state.get("previa_documentacao", {})
    metadados = state.get("metadados_catalogo", {})

    # --- Se já havia erro crítico, apenas consolida ---
    if state.get("status_final") == "erro":
        logger.error(
            "[supervisor_node] ✗ Grafo encerrado com ERRO — %d erro(s) encontrado(s)",
            len(erros),
        )
        for i, erro in enumerate(erros, 1):
            logger.error("[supervisor_node]   Erro %d: %s", i, erro)
        return {
            "status_final": "erro",
            "etapa_atual": "supervisor_node",
        }

    # --- Valida se a persistência aconteceu ---
    problemas = []

    if not id_previa:
        problemas.append("ID da prévia não gerado — documentos_gerados_previas pode não ter sido salvo")
    if not id_metadados:
        problemas.append("ID dos metadados não gerado — componentes_catalogados_metadados pode não ter sido salvo")

    if problemas:
        erros.extend(problemas)
        logger.warning(
            "[supervisor_node] ⚠ Execução com problemas parciais:"
        )
        for problema in problemas:
            logger.warning("[supervisor_node]   • %s", problema)

        return {
            "erros": erros,
            "status_final": "erro_parcial",
            "etapa_atual": "supervisor_node",
        }

    # --- Tudo ok: emite resumo de sucesso ---
    status_final = "sucesso" if not erros else "sucesso_com_avisos"

    logger.info("[supervisor_node] ✓ GRAFO EXECUTADO COM SUCESSO")
    logger.info("-" * 55)
    logger.info(
        "[supervisor_node] ✓ Componente  : '%s'",
        metadados.get("component_name"),
    )
    logger.info(
        "[supervisor_node] ✓ Evento      : '%s'",
        metadados.get("event_id"),
    )
    logger.info(
        "[supervisor_node] ✓ ID prévia   : %s → documentos_gerados_previas",
        id_previa,
    )
    logger.info(
        "[supervisor_node] ✓ ID metadados: %s → componentes_catalogados_metadados",
        id_metadados,
    )
    logger.info(
        "[supervisor_node] ✓ Status      : %s",
        status_final,
    )

    if erros:
        logger.warning(
            "[supervisor_node] ⚠ %d aviso(s) durante execução:", len(erros)
        )
        for aviso in erros:
            logger.warning("[supervisor_node]   • %s", aviso)

    logger.info("=" * 55)
    logger.info(
        "[supervisor_node] Verifique os dados no MongoDB Compass:"
    )
    logger.info(
        "[supervisor_node]   DB: atlas_documentacao_agente"
    )
    logger.info(
        "[supervisor_node]   → documentos_gerados_previas"
    )
    logger.info(
        "[supervisor_node]   → componentes_catalogados_metadados"
    )
    logger.info("=" * 55)

    return {
        "erros": erros,
        "status_final": status_final,
        "etapa_atual": "supervisor_node",
    }