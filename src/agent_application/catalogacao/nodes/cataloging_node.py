"""
nodes/cataloging_node.py
--------------------------
Quarto nó do grafo (Fase 7) — gera os metadados técnicos via LLM OpenAI,
percorrendo o checklist fixo (libs, segurança, bancos, mensageria,
tecnologia, Sicredi Flow, S3, imagem).

Fase 3-6: recebia JSON com metadados de negócio já prontos.
Fase 7: os campos de negócio (team_id, criticidade, environment,
        time_responsavel, projeto, tribo, status_aplicacao) NÃO EXISTEM
        mais na entrada — ficam explicitamente None, pois não podem ser
        inferidos apenas do código-fonte.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from src.agent_application.prompts.prompts_catalog_document import (
    SYSTEM_CHECKLIST_TECNICO,
    montar_prompt_checklist_tecnico,
)
from src.agent_application.state import DocumentacaoState
from src.settings import get_settings

logger = logging.getLogger(__name__)


def _limpar_json_llm(texto: str) -> str:
    """Remove blocos de markdown que a LLM às vezes inclui por engano."""
    texto = texto.strip()
    if texto.startswith("```"):
        linhas = texto.split("\n")
        texto = "\n".join(linhas[1:-1])
    return texto


def _chamar_llm_checklist(repo_data: dict[str, Any]) -> dict[str, Any]:
    """
    Chama a LLM OpenAI para preencher o checklist técnico do repositório.

    Args:
        repo_data: dados buscados pelo repository_fetch_node

    Returns:
        dict estruturado no formato da collection
        componentes_catalogados_metadados, com campos de negócio
        explicitamente None
    """
    settings = get_settings()

    llm = ChatOpenAI(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
    )

    mensagens = [
        SystemMessage(content=SYSTEM_CHECKLIST_TECNICO),
        HumanMessage(content=montar_prompt_checklist_tecnico(repo_data)),
    ]

    logger.info(
        "[cataloging_node] Chamando LLM '%s' para o checklist técnico...",
        settings.openai_model,
    )

    resposta = llm.invoke(mensagens)
    texto_limpo = _limpar_json_llm(resposta.content)

    try:
        checklist = json.loads(texto_limpo)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM retornou JSON inválido para o checklist: {str(exc)}\n"
            f"Conteúdo retornado: {texto_limpo[:200]}..."
        ) from exc

    # --- Campos de rastreabilidade ---
    checklist["event_id"] = repo_data.get("event_id")
    checklist["repository"] = repo_data.get("repository_url")
    checklist["repository_owner"] = repo_data.get("owner")
    checklist["catalogado_em"] = datetime.now(timezone.utc).isoformat()
    checklist["catalogado_por"] = settings.openai_model
    checklist["tokens_utilizados"] = resposta.usage_metadata

    # --- Campos de negócio: explicitamente None (Fase 7) ---
    # Não existem no repositório de código — dependiam do JSON do
    # inventário, que não faz mais parte desta entrada.
    checklist["team_id"] = None
    checklist["time_responsavel"] = None
    checklist["projeto"] = None
    checklist["tribo"] = None
    checklist["criticidade"] = None
    checklist["environment"] = None
    checklist["status_aplicacao"] = None
    checklist["categoria_aplicacao"] = None

    return checklist


def cataloging_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Gera os metadados técnicos (checklist) do repositório via LLM OpenAI.

    Args:
        state: Estado atual com repo_data validado e secoes_documentacao
               já geradas

    Returns:
        dict com metadados_catalogo preenchido pela LLM
    """
    logger.info("-" * 55)
    logger.info("[cataloging_node] Gerando checklist técnico via LLM OpenAI")
    logger.info("-" * 55)

    if state.get("status_final") == "erro":
        logger.warning(
            "[cataloging_node] ⚠ Erro detectado no estado — pulando catalogação"
        )
        return {"etapa_atual": "cataloging_node"}

    repo_data = state["repo_data"]
    erros = list(state.get("erros", []))

    try:
        metadados = _chamar_llm_checklist(repo_data)

        logger.info(
            "[cataloging_node] ✓ Checklist gerado para: '%s'",
            metadados.get("component_name"),
        )
        for item in [
            "seguranca",
            "bancos_de_dados",
            "mensageria",
            "tecnologia_principal",
            "uso_sicredi_flow",
            "uso_s3",
            "containerizacao",
        ]:
            resultado_item = metadados.get(item, {})
            logger.info(
                "[cataloging_node]   • %s: %s",
                item,
                resultado_item.get("status", "?") if isinstance(resultado_item, dict) else resultado_item,
            )
        logger.info(
            "[cataloging_node] ✓ Catalogado por: '%s'",
            metadados.get("catalogado_por"),
        )
        logger.info("[cataloging_node] ✓ Seguindo para persistence_node")

        return {
            "metadados_catalogo": metadados,
            "erros": erros,
            "etapa_atual": "cataloging_node",
        }

    except Exception as exc:
        erro = f"Erro ao gerar checklist técnico: {str(exc)}"
        logger.error("[cataloging_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "cataloging_node",
        }