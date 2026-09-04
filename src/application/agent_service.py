"""
application/agent_service.py
------------------------------
Orquestrador da aplicação — ponto de entrada do grafo LangGraph.

Fase 1: executava um teste de conexão simples com o MongoDB.
Fase 2: executa o grafo LangGraph completo com dados mockados.

Responsabilidades:
  1. Carregar o JSON de entrada (mock por ora, Kafka na Fase 4)
  2. Criar o estado inicial do grafo
  3. Compilar e executar o grafo
  4. Exibir o resultado final
"""

import json
import logging
from pathlib import Path
from typing import Any

from src.application.agents.documentacao.graph import criar_grafo_documentacao
from src.application.agents.documentacao.state import criar_estado_inicial

logger = logging.getLogger(__name__)

# Caminho do JSON mockado — na Fase 4 será substituído pelo consumer Kafka
MOCK_INPUT_PATH = Path(__file__).parent.parent.parent / "mock_input" / "component_event.json"


def _carregar_json_entrada() -> dict[str, Any]:
    """
    Carrega o JSON de entrada do arquivo mock.

    Na Fase 4 esta função será substituída pelo consumer Kafka
    que receberá o JSON do tópico atlas-processamento-assincrono-dados.
    """
    if not MOCK_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo mock não encontrado: {MOCK_INPUT_PATH}\n"
            "Crie o arquivo mock_input/component_event.json"
        )

    logger.info("Carregando JSON de entrada: %s", MOCK_INPUT_PATH.name)

    with open(MOCK_INPUT_PATH, encoding="utf-8") as f:
        return json.load(f)


def executar_grafo() -> None:
    """
    Executa o grafo LangGraph de documentação e catalogação.
    """
    logger.info("=" * 60)
    logger.info("ATLAS DOCUMENTACAO AGENT — FASE 2")
    logger.info("Grafo LangGraph com nós mockados")
    logger.info("=" * 60)

    # --- 1. Carrega o JSON de entrada ---
    json_entrada = _carregar_json_entrada()

    component_name = (
        json_entrada.get("application", {}).get("component_name", "N/A")
    )
    logger.info("Componente a processar: '%s'", component_name)

    # --- 2. Cria o estado inicial ---
    estado_inicial = criar_estado_inicial(json_entrada)
    logger.info("Estado inicial criado — iniciando grafo")

    # --- 3. Compila e executa o grafo ---
    grafo = criar_grafo_documentacao()
    estado_final = grafo.invoke(estado_inicial)

    # --- 4. Exibe o resultado final ---
    logger.info("")
    logger.info("=" * 60)
    logger.info("RESULTADO FINAL DO GRAFO")
    logger.info("=" * 60)
    logger.info("Status       : %s", estado_final.get("status_final"))
    logger.info("Última etapa : %s", estado_final.get("etapa_atual"))
    logger.info("ID prévia    : %s", estado_final.get("id_mongodb_previa"))
    logger.info("ID metadados : %s", estado_final.get("id_mongodb_metadados"))

    erros = estado_final.get("erros", [])
    if erros:
        logger.warning("Avisos/Erros : %d ocorrência(s)", len(erros))
        for erro in erros:
            logger.warning("  • %s", erro)
    else:
        logger.info("Erros        : nenhum")

    logger.info("=" * 60)