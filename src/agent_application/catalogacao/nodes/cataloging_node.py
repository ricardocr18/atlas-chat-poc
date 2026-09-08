"""
nodes/cataloging_node.py
--------------------------
Terceiro nó do grafo — gera metadados estruturados via LLM OpenAI.

Fase 2: extraía metadados diretamente dos campos do JSON.
Fase 3: chama a LLM OpenAI para gerar metadados enriquecidos
        em formato JSON estruturado, com classificações e sugestões
        que vão além do que está explícito nos dados de entrada.

Diferença entre os dois nós de geração:
  documentation_node → pede texto narrativo (leitura humana)
  cataloging_node    → pede JSON estruturado (leitura de máquina)

Por isso o prompt de catalogação instrui a LLM a retornar
APENAS JSON válido, que é então parseado e salvo no MongoDB.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.agent_application.prompts.prompts_catalog_document import (
    SYSTEM_CATALOGACAO,
    montar_prompt_catalogacao,
)
from src.agent_application.state import DocumentacaoState
from src.settings import get_settings

logger = logging.getLogger(__name__)


def _chamar_llm_catalogacao(json_entrada: dict[str, Any]) -> dict[str, Any]:
    """
    Chama a LLM OpenAI para gerar os metadados estruturados de catálogo.

    Diferente do documentation_node, aqui a LLM é instruída a retornar
    JSON válido — que é parseado e usado diretamente como documento
    a ser salvo na collection componentes_catalogados_metadados.

    Args:
        json_entrada: JSON normalizado do inventário

    Returns:
        dict estruturado no formato da collection
        componentes_catalogados_metadados
    """
    settings = get_settings()
    processing = json_entrada.get("processing", {})

    # --- Inicializa o cliente OpenAI via LangChain ---
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
    )

    # --- Monta as mensagens do prompt ---
    mensagens = [
        SystemMessage(content=SYSTEM_CATALOGACAO),
        HumanMessage(content=montar_prompt_catalogacao(json_entrada)),
    ]

    logger.info(
        "[cataloging_node] Chamando LLM '%s' para gerar metadados...",
        settings.openai_model,
    )

    # --- Chama a LLM ---
    resposta = llm.invoke(mensagens)
    texto_retornado = resposta.content.strip()

    logger.info(
        "[cataloging_node] ✓ LLM respondeu — parseando JSON retornado..."
    )

    # --- Parseia o JSON retornado pela LLM ---
    # Remove possíveis blocos de markdown caso a LLM ignore a instrução
    if texto_retornado.startswith("```"):
        linhas = texto_retornado.split("\n")
        texto_retornado = "\n".join(linhas[1:-1])

    try:
        metadados = json.loads(texto_retornado)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM retornou JSON inválido: {str(exc)}\n"
            f"Conteúdo retornado: {texto_retornado[:200]}..."
        ) from exc

    # --- Adiciona campos de rastreabilidade ---
    metadados["catalogado_em"] = datetime.now(timezone.utc).isoformat()
    metadados["catalogado_por"] = settings.openai_model
    metadados["event_id"] = processing.get("event_id")
    metadados["transaction_id"] = processing.get("transaction_id")
    metadados["data_evento"] = processing.get("event_date")
    metadados["tokens_utilizados"] = resposta.usage_metadata

    return metadados


def cataloging_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Gera os metadados estruturados de catálogo via LLM OpenAI.

    Args:
        state: Estado atual com json_entrada validado e
               previa_documentacao já gerada

    Returns:
        dict com metadados_catalogo preenchido pela LLM
    """
    logger.info("-" * 55)
    logger.info("[cataloging_node] Gerando metadados via LLM OpenAI")
    logger.info("-" * 55)

    if state.get("status_final") == "erro":
        logger.warning(
            "[cataloging_node] ⚠ Erro detectado no estado — pulando catalogação"
        )
        return {"etapa_atual": "cataloging_node"}

    json_entrada = state["json_entrada"]
    erros = list(state.get("erros", []))

    try:
        metadados = _chamar_llm_catalogacao(json_entrada)

        logger.info(
            "[cataloging_node] ✓ Metadados gerados para: '%s'",
            metadados.get("component_name"),
        )
        logger.info(
            "[cataloging_node] ✓ Maturidade: '%s' | Documentação: '%s'",
            metadados.get("classificacao_maturidade"),
            metadados.get("nivel_documentacao"),
        )
        logger.info(
            "[cataloging_node] ✓ Tags geradas: %s",
            metadados.get("tags"),
        )
        logger.info(
            "[cataloging_node] ✓ Catalogado por: '%s'",
            metadados.get("catalogado_por"),
        )
        logger.info(
            "[cataloging_node] ✓ Seguindo para persistence_node"
        )

        return {
            "metadados_catalogo": metadados,
            "erros": erros,
            "etapa_atual": "cataloging_node",
        }

    except Exception as exc:
        erro = f"Erro ao chamar LLM para catalogação: {str(exc)}"
        logger.error("[cataloging_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "cataloging_node",
        }