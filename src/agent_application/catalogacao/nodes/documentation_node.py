"""
nodes/documentation_node.py
-----------------------------
Segundo nó do grafo — gera a prévia de documentação via LLM OpenAI.

Fase 2: gerava documentação mockada extraindo campos do JSON.
Fase 3: chama a LLM OpenAI via LangChain para gerar documentação
        rica, contextualizada e tecnicamente precisa.

O que muda em relação à Fase 2:
  - A função _gerar_previa_mockada() foi substituída por _chamar_llm_documentacao()
  - O campo "gerado_por" agora mostra o modelo real utilizado
  - O conteúdo gerado é inteligente, não apenas extração de campos

O que NÃO muda:
  - A interface do nó (entrada/saída de estado) é idêntica
  - O persistence_node salva da mesma forma
  - O supervisor_node valida da mesma forma
"""

import logging
from datetime import datetime, timezone
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.agent_application.prompts.prompts_catalog_document import (
    SYSTEM_DOCUMENTACAO,
    montar_prompt_documentacao,
)
from src.agent_application.state import DocumentacaoState
from src.settings import get_settings

logger = logging.getLogger(__name__)


def _chamar_llm_documentacao(json_entrada: dict[str, Any]) -> dict[str, Any]:
    """
    Chama a LLM OpenAI para gerar a prévia de documentação.

    Utiliza LangChain como camada de abstração sobre a OpenAI API.
    O SystemMessage define o papel da LLM, o HumanMessage fornece
    os dados do componente e a instrução de geração.

    Args:
        json_entrada: JSON normalizado do inventário

    Returns:
        dict estruturado no formato da collection documentos_gerados_previas
    """
    settings = get_settings()
    application = json_entrada.get("application", {})
    processing = json_entrada.get("processing", {})

    # --- Inicializa o cliente OpenAI via LangChain ---
    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
    )

    # --- Monta as mensagens do prompt ---
    mensagens = [
        SystemMessage(content=SYSTEM_DOCUMENTACAO),
        HumanMessage(content=montar_prompt_documentacao(json_entrada)),
    ]

    logger.info(
        "[documentation_node] Chamando LLM '%s' para gerar documentação...",
        settings.openai_model,
    )

    # --- Chama a LLM ---
    resposta = llm.invoke(mensagens)
    texto_gerado = resposta.content

    logger.info(
        "[documentation_node] ✓ LLM respondeu — %d caracteres gerados",
        len(texto_gerado),
    )

    # --- Estrutura o retorno no formato da collection ---
    people = json_entrada.get("people", {})

    return {
        "event_id": processing.get("event_id"),
        "transaction_id": processing.get("transaction_id"),
        "component_name": application.get("component_name"),
        "application_name": application.get("application_name"),
        "titulo": f"{application.get('component_name')} — Prévia de Documentação",
        "descricao_gerada": texto_gerado,
        "tipo_aplicacao": application.get("tipo_aplicacao"),
        "environment": application.get("environment"),
        "repository": application.get("repository"),
        "responsaveis": {
            "tech_leads": people.get("tech_leads", []),
            "aprovadores": people.get("aprovadores", []),
            "arquitetos": people.get("arquitetos", []),
            "desenvolvedores": people.get("desenvolvedores", []),
            "qa": people.get("qa", []),
        },
        "fonte_evento": processing.get("event_id"),
        "tipo_evento": processing.get("event_type"),
        "data_evento": processing.get("event_date"),
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "gerado_por": settings.openai_model,
        "tokens_utilizados": resposta.usage_metadata,
    }


def documentation_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Gera a prévia de documentação do componente via LLM OpenAI.

    Args:
        state: Estado atual com json_entrada validado

    Returns:
        dict com previa_documentacao preenchida pela LLM
    """
    logger.info("-" * 55)
    logger.info("[documentation_node] Gerando prévia via LLM OpenAI")
    logger.info("-" * 55)

    if state.get("status_final") == "erro":
        logger.warning(
            "[documentation_node] ⚠ Erro detectado no estado — pulando geração"
        )
        return {"etapa_atual": "documentation_node"}

    json_entrada = state["json_entrada"]
    erros = list(state.get("erros", []))

    try:
        previa = _chamar_llm_documentacao(json_entrada)

        logger.info(
            "[documentation_node] ✓ Prévia gerada para: '%s'",
            previa.get("component_name"),
        )
        logger.info(
            "[documentation_node] ✓ Gerado por: '%s'",
            previa.get("gerado_por"),
        )
        logger.info(
            "[documentation_node] ✓ Seguindo para cataloging_node"
        )

        return {
            "previa_documentacao": previa,
            "erros": erros,
            "etapa_atual": "documentation_node",
        }

    except Exception as exc:
        erro = f"Erro ao chamar LLM para documentação: {str(exc)}"
        logger.error("[documentation_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "documentation_node",
        }