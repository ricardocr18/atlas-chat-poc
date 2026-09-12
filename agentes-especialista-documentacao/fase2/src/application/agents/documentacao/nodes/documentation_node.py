"""
nodes/documentation_node.py
-----------------------------
Segundo nó do grafo — gera a prévia de documentação do componente.

Responsabilidade: receber o JSON validado e produzir um documento
de prévia estruturado para ser salvo na collection
documentos_gerados_previas do MongoDB.

Estado atual (Fase 2): gera documentação MOCKADA com dados
extraídos diretamente do JSON de entrada.

Fase 3: este nó será atualizado para chamar a LLM OpenAI,
que receberá o JSON como contexto e gerará a documentação
de forma inteligente e descritiva. A interface do nó
(entrada/saída de estado) não muda — só o interior.

Separação de responsabilidades:
  - Este nó APENAS gera a prévia (dict Python)
  - Ele NÃO salva no MongoDB — isso é responsabilidade
    exclusiva do persistence_node
"""

import logging
from datetime import datetime, timezone
from typing import Any

from src.application.agents.documentacao.state import DocumentacaoState

logger = logging.getLogger(__name__)


def _gerar_previa_mockada(json_entrada: dict[str, Any]) -> dict[str, Any]:
    """
    Gera uma prévia de documentação estruturada a partir do JSON.

    Na Fase 3 esta função será substituída por uma chamada
    à LLM OpenAI via LangChain.

    Args:
        json_entrada: JSON normalizado do inventário

    Returns:
        dict estruturado no formato da collection documentos_gerados_previas
    """
    application = json_entrada.get("application", {})
    team = json_entrada.get("team", {})
    people = json_entrada.get("people", {})
    processing = json_entrada.get("processing", {})
    devconsole = json_entrada.get("devconsole", {})
    gitlab = json_entrada.get("gitlab", {})

    component_name = application.get("component_name", "N/A")
    app_name = application.get("application_name", "N/A")

    # Descrição mockada — na Fase 3 será gerada pela LLM
    descricao = (
        f"O componente {component_name} é uma "
        f"{application.get('tipo_aplicacao', 'aplicação')} "
        f"{application.get('categoria_aplicacao', '')} "
        f"de criticidade {devconsole.get('criticality', 'N/A')}, "
        f"pertencente ao {team.get('projeto', 'N/A')} "
        f"da {team.get('tribo', 'N/A')}. "
        f"Desenvolvida pelo {team.get('time_responsavel', 'N/A')}, "
        f"a aplicação está {application.get('status_aplicacao', 'N/A')} "
        f"no ambiente {application.get('environment', 'N/A')} "
        f"e hospedada no repositório {application.get('repository', 'N/A')}. "
        f"O repositório possui {gitlab.get('branch_count', 0)} branches "
        f"e está na versão {devconsole.get('version', 'N/A')}."
    )

    return {
        "event_id": processing.get("event_id"),
        "transaction_id": processing.get("transaction_id"),
        "component_name": component_name,
        "application_name": app_name,
        "titulo": f"{component_name} — Prévia de Documentação",
        "descricao_gerada": descricao,
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
        "arquivos_detectados": gitlab.get("repository_tree", []),
        "fonte_evento": processing.get("event_id"),
        "tipo_evento": processing.get("event_type"),
        "data_evento": processing.get("event_date"),
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "gerado_por": "mock",  # Fase 3: será "openai/gpt-4o"
    }


def documentation_node(state: DocumentacaoState) -> dict[str, Any]:
    """
    Gera a prévia de documentação do componente.

    Lê o json_entrada do estado, gera a prévia estruturada
    e a escreve de volta no estado para o próximo nó usar.

    Args:
        state: Estado atual com json_entrada validado

    Returns:
        dict com previa_documentacao preenchida
    """
    logger.info("-" * 55)
    logger.info("[documentation_node] Gerando prévia de documentação")
    logger.info("-" * 55)

    # Se houve erro no nó anterior, não processa
    if state.get("status_final") == "erro":
        logger.warning(
            "[documentation_node] ⚠ Erro detectado no estado — pulando geração"
        )
        return {"etapa_atual": "documentation_node"}

    json_entrada = state["json_entrada"]
    erros = list(state.get("erros", []))

    try:
        previa = _gerar_previa_mockada(json_entrada)

        logger.info(
            "[documentation_node] ✓ Prévia gerada para: '%s'",
            previa.get("component_name"),
        )
        logger.info(
            "[documentation_node] ✓ Título: '%s'",
            previa.get("titulo"),
        )
        logger.info(
            "[documentation_node] ✓ Gerado por: '%s' (Fase 3: será OpenAI)",
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
        erro = f"Erro ao gerar prévia: {str(exc)}"
        logger.error("[documentation_node] ✗ %s", erro)
        erros.append(erro)
        return {
            "erros": erros,
            "status_final": "erro",
            "etapa_atual": "documentation_node",
        }