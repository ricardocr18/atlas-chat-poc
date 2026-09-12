"""
nodes/cataloging_node.py
--------------------------
Terceiro nó do grafo — gera os metadados estruturados de catálogo.

Responsabilidade: receber o JSON validado e produzir os metadados
estruturados para serem salvos na collection
componentes_catalogados_metadados do MongoDB.

Diferença em relação ao documentation_node:
  - documentation_node → gera texto descritivo (prévia legível)
  - cataloging_node    → gera metadados estruturados (dados para busca,
                          filtros, relatórios e integração com outros sistemas)

Estado atual (Fase 2): extrai e estrutura metadados MOCKADOS
diretamente do JSON de entrada.

Fase 3: chamará a LLM OpenAI para enriquecer os metadados,
detectar padrões, sugerir tags adicionais e classificar
o componente de forma mais inteligente.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from src.application.agents.documentacao.state import DocumentacaoState

logger = logging.getLogger(__name__)


def _gerar_metadados_mockados(json_entrada: dict[str, Any]) -> dict[str, Any]:
    """
    Extrai e estrutura os metadados do componente a partir do JSON.

    Na Fase 3 esta função será enriquecida com análise da LLM,
    que poderá detectar padrões no repositório, sugerir tags,
    classificar a maturidade do componente, etc.

    Args:
        json_entrada: JSON normalizado do inventário

    Returns:
        dict estruturado no formato da collection
        componentes_catalogados_metadados
    """
    application = json_entrada.get("application", {})
    team = json_entrada.get("team", {})
    people = json_entrada.get("people", {})
    processing = json_entrada.get("processing", {})
    devconsole = json_entrada.get("devconsole", {})
    gitlab = json_entrada.get("gitlab", {})
    sources = json_entrada.get("sources", {})

    # Tags geradas automaticamente — na Fase 3 a LLM sugerirá mais
    tags = [
        application.get("tipo_aplicacao", ""),
        application.get("categoria_aplicacao", ""),
        application.get("environment", "").lower(),
        devconsole.get("cloud_provider", ""),
        team.get("tribo", "").lower().replace(" ", "-"),
    ]
    tags = [t for t in tags if t]  # remove vazios

    return {
        # --- Identificação ---
        "event_id": processing.get("event_id"),
        "transaction_id": processing.get("transaction_id"),
        "component_name": application.get("component_name"),
        "application_name": application.get("application_name"),

        # --- Classificação ---
        "tipo_aplicacao": application.get("tipo_aplicacao"),
        "categoria_aplicacao": application.get("categoria_aplicacao"),
        "criticidade": devconsole.get("criticality"),
        "cloud_provider": devconsole.get("cloud_provider"),
        "tags": tags,

        # --- Time e Pessoas ---
        "team_id": team.get("team_id"),
        "time_responsavel": team.get("time_responsavel"),
        "projeto": team.get("projeto"),
        "tribo": team.get("tribo"),
        "tech_leads": people.get("tech_leads", []),
        "aprovadores": people.get("aprovadores", []),
        "arquitetos": people.get("arquitetos", []),

        # --- Repositório ---
        "repository": application.get("repository"),
        "default_branch": application.get("default_branch"),
        "branch_count": gitlab.get("branch_count"),
        "gitlab_host": gitlab.get("host"),

        # --- Status ---
        "status_aplicacao": application.get("status_aplicacao"),
        "environment": application.get("environment"),
        "version": devconsole.get("version"),

        # --- Fontes de dados ---
        "fontes": {
            "devconsole": sources.get("devconsole"),
            "cmdb": sources.get("cmdb"),
            "gitlab": sources.get("gitlab"),
        },

        # --- Rastreabilidade ---
        "tipo_evento": processing.get("event_type"),
        "data_evento": processing.get("event_date"),
        "catalogado_em": datetime.now(timezone.utc).isoformat(),
        "catalogado_por": "mock",  # Fase 3: será "openai/gpt-4o"
    }


def cataloging_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Gera os metadados estruturados de catálogo do componente.

    Lê o json_entrada do estado, estrutura os metadados
    e os escreve no estado para o persistence_node salvar
    na collection correta.

    Args:
        state: Estado atual com json_entrada validado e
               previa_documentacao já gerada

    Returns:
        dict com metadados_catalogo preenchido
    """
    logger.info("-" * 55)
    logger.info("[cataloging_node] Gerando metadados de catálogo")
    logger.info("-" * 55)

    # Se houve erro em nó anterior, não processa
    if state.get("status_final") == "erro":
        logger.warning(
            "[cataloging_node] ⚠ Erro detectado no estado — pulando catalogação"
        )
        return {"etapa_atual": "cataloging_node"}

    json_entrada = state["json_entrada"]
    erros = list(state.get("erros", []))

    try:
        metadados = _gerar_metadados_mockados(json_entrada)

        logger.info(
            "[cataloging_node] ✓ Metadados gerados para: '%s'",
            metadados.get("component_name"),
        )
        logger.info(
            "[cataloging_node] ✓ Criticidade: '%s' | Cloud: '%s'",
            metadados.get("criticidade"),
            metadados.get("cloud_provider"),
        )
        logger.info(
            "[cataloging_node] ✓ Tags geradas: %s",
            metadados.get("tags"),
        )
        logger.info(
            "[cataloging_node] ✓ Catalogado por: '%s' (Fase 3: será OpenAI)",
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
        erro = f"Erro ao gerar metadados: {str(exc)}"
        logger.error("[cataloging_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "cataloging_node",
        }