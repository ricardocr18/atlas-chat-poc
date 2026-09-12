"""
agent_application/agent_service.py
-------------------------------------
Orquestrador da aplicação — ponto de entrada do grafo LangGraph.

Histórico de evolução:
  Fase 1: executava teste de conexão simples com MongoDB
  Fase 2: executava o grafo com JSON mockado direto no código
  Fase 3: executava o grafo lendo JSON de arquivo local
  Fase 4: suporta três modos de entrada controlados por INPUT_MODE:
            file       → lê mock_input/component_event.json
            mock_kafka → consumer Kafka simulado com JSON local
            kafka      → consumer Kafka real (broker da Sicredi)

Responsabilidades:
  1. Verificar o modo de entrada configurado (INPUT_MODE)
  2. Direcionar para o mecanismo correto de recebimento do JSON
  3. Executar o grafo LangGraph com o JSON recebido
  4. Exibir o resultado final
"""

import json
import logging
from pathlib import Path
from typing import Any

from src.agent_application.graph import criar_grafo_documentacao
from src.agent_application.state import criar_estado_inicial
from src.settings import get_settings

logger = logging.getLogger(__name__)

# Caminho do JSON mockado — usado nos modos file e mock_kafka
MOCK_INPUT_PATH = (
    Path(__file__).parent.parent.parent / "mock_input" / "component_event.json"
)


def _carregar_json_arquivo() -> dict[str, Any]:
    """
    Carrega o JSON de entrada do arquivo mock local.
    Usado quando INPUT_MODE=file.
    """
    if not MOCK_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo mock não encontrado: {MOCK_INPUT_PATH}\n"
            "Crie o arquivo mock_input/component_event.json"
        )

    logger.info("Carregando JSON de entrada: %s", MOCK_INPUT_PATH.name)

    with open(MOCK_INPUT_PATH, encoding="utf-8") as f:
        return json.load(f)


def _processar_mensagem(json_entrada: dict[str, Any]) -> None:
    """
    Callback acionado pelo consumer Kafka ao receber uma mensagem.

    Passado como callback para o consumer — ele a chama com o JSON
    deserializado cada vez que uma mensagem chega no tópico.
    Também chamada diretamente no modo file.
    """
    component_name = (
        json_entrada.get("application", {}).get("component_name", "N/A")
    )
    logger.info("Componente a processar: '%s'", component_name)

    estado_inicial = criar_estado_inicial(json_entrada)
    grafo = criar_grafo_documentacao()
    estado_final = grafo.invoke(estado_inicial)

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


def executar_grafo() -> None:
    """
    Ponto de entrada principal — seleciona o modo de operação.

    Lê INPUT_MODE do .env e direciona para o mecanismo correto:
      file       → carrega JSON local e processa uma vez
      mock_kafka → simula consumer Kafka com JSON local
      kafka      → consumer Kafka real (loop contínuo)
    """
    settings = get_settings()
    modo = settings.input_mode.lower()

    logger.info("=" * 60)
    logger.info("ATLAS DOCUMENTACAO AGENT — FASE 4")
    logger.info("Modo de entrada: %s", modo.upper())
    logger.info("=" * 60)

    if modo == "file":
        logger.info("Lendo JSON do arquivo local...")
        json_entrada = _carregar_json_arquivo()
        _processar_mensagem(json_entrada)

    elif modo in ("mock_kafka", "kafka"):
        from src.infrastructure.kafka import iniciar_consumer
        iniciar_consumer(_processar_mensagem)

    else:
        raise ValueError(
            f"INPUT_MODE='{modo}' inválido.\n"
            "Valores aceitos: 'file', 'mock_kafka', 'kafka'"
        )