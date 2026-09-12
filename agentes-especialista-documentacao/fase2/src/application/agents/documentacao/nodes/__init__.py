"""
nodes/input_node.py
--------------------
Primeiro nó do grafo — valida e carrega o JSON de entrada.

Responsabilidade única: garantir que o JSON recebido tem
todos os campos obrigatórios antes de seguir para os próximos nós.

Por que validar aqui?
  Se o JSON chegar incompleto ou malformado, é muito melhor
  falhar no primeiro nó com uma mensagem clara do que deixar
  o erro aparecer no meio do grafo ou pior — salvar dados
  incompletos no MongoDB.

Na Fase 4 (Kafka): este nó receberá o JSON deserializado
do tópico atlas-processamento-assincrono-dados. A lógica
de validação aqui não muda — só muda quem chama este nó.
"""

import logging
from typing import Any

from src.application.agents.documentacao.state import DocumentacaoState

logger = logging.getLogger(__name__)

# Campos obrigatórios que o JSON do inventário deve conter
CAMPOS_OBRIGATORIOS = [
    "team",
    "application",
    "processing",
    "completeness",
]


def input_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Valida o JSON de entrada e prepara o estado para os próximos nós.

    Fluxo:
      1. Loga o início do processamento
      2. Verifica se os campos obrigatórios estão presentes
      3. Verifica se o documento está completo (completeness.status)
      4. Extrai informações-chave para log
      5. Atualiza o estado com o resultado da validação

    Args:
        state: Estado atual do grafo com json_entrada preenchido

    Returns:
        dict com atualizações para o estado do grafo.
        O LangGraph faz merge automático com o estado atual.
    """
    logger.info("=" * 55)
    logger.info("[input_node] Iniciando validação do documento")
    logger.info("=" * 55)

    json_entrada = state["json_entrada"]
    erros = list(state.get("erros", []))

    # --- Validação 1: campos obrigatórios ---
    campos_faltando = [
        campo for campo in CAMPOS_OBRIGATORIOS
        if campo not in json_entrada
    ]

    if campos_faltando:
        erro = f"Campos obrigatórios ausentes: {campos_faltando}"
        logger.error("[input_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "input_node",
        }

    # --- Validação 2: completeness do documento ---
    completeness = json_entrada.get("completeness", {})
    if completeness.get("status") != "COMPLETE":
        campos_missing = completeness.get("missing_fields", [])
        erro = f"Documento incompleto. Campos faltando: {campos_missing}"
        logger.warning("[input_node] ⚠ %s", erro)
        erros.append(erro)

    # --- Log das informações principais ---
    application = json_entrada.get("application", {})
    team = json_entrada.get("team", {})
    processing = json_entrada.get("processing", {})

    logger.info(
        "[input_node] ✓ Componente: '%s' | App: '%s'",
        application.get("component_name"),
        application.get("application_name"),
    )
    logger.info(
        "[input_node] ✓ Time: '%s' | Tribo: '%s'",
        team.get("time_responsavel"),
        team.get("tribo"),
    )
    logger.info(
        "[input_node] ✓ Evento: '%s' | Tipo: '%s'",
        processing.get("event_id"),
        processing.get("event_type"),
    )
    logger.info(
        "[input_node] ✓ Completeness: '%s'",
        completeness.get("status"),
    )
    logger.info("[input_node] ✓ Validação concluída — seguindo para documentation_node")

    return {
        "erros": erros,
        "etapa_atual": "input_node",
    }