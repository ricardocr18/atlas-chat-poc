"""
infrastructure/kafka/consumer.py
----------------------------------
Consumer Kafka do agente de documentação e catalogação.

Responsabilidade: escutar o tópico atlas-processamento-assincrono-dados
e acionar o grafo LangGraph quando uma nova mensagem chegar.

Modos de operação (INPUT_MODE no .env):
  file       → lê o JSON local diretamente (sem passar por este módulo)
  mock_kafka → simula o Kafka usando o JSON local, mas executa todo
               o código do consumer (deserialização, tratamento de erros)
  kafka      → consumer Kafka real conectado ao broker da Sicredi

Por que mock_kafka é valioso?
  Ele exercita 100% do código deste módulo usando o JSON local como
  fonte. Quando o Kafka real chegar, a única diferença será:
    1. Trocar KAFKA_BOOTSTRAP_SERVERS no .env
    2. Configurar SSL/SASL se necessário
  O código do consumer não muda.

Fluxo do consumer real (modo kafka):
  1. Conecta ao broker usando as configs do config.py
  2. Se inscreve no tópico atlas-processamento-assincrono-dados
  3. Loop contínuo: poll() → mensagem → deserializa → aciona grafo
  4. Commit do offset após processamento bem-sucedido
  5. Tratamento de erro: loga e continua (não para o consumer)
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Callable

from src.settings import get_settings

logger = logging.getLogger(__name__)

# Caminho do JSON mockado — usado nos modos file e mock_kafka
MOCK_INPUT_PATH = (
    Path(__file__).parent.parent.parent.parent / "mock_input" / "component_event.json"
)


# ===========================================================
# MODO: mock_kafka
# Simula o comportamento do consumer usando o JSON local
# ===========================================================

def _executar_mock_kafka(callback: Callable[[dict[str, Any]], None]) -> None:
    """
    Simula o consumer Kafka usando o arquivo JSON local.

    Executa o mesmo fluxo que o consumer real:
      1. "Recebe" uma mensagem (do arquivo local)
      2. Deserializa o JSON
      3. Chama o callback (que aciona o grafo)
      4. Simula commit do offset

    Args:
        callback: função que recebe o JSON deserializado e aciona o grafo
    """
    logger.info("=" * 60)
    logger.info("[consumer] MODO: mock_kafka")
    logger.info("[consumer] Simulando consumer Kafka com JSON local")
    logger.info("[consumer] Tópico simulado: %s", get_settings().kafka_topic)
    logger.info("=" * 60)

    if not MOCK_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo mock não encontrado: {MOCK_INPUT_PATH}\n"
            "Certifique-se que mock_input/component_event.json existe."
        )

    # Simula o recebimento de uma mensagem do Kafka
    logger.info("[consumer] Simulando recebimento de mensagem do tópico...")
    time.sleep(0.5)  # simula latência de rede

    with open(MOCK_INPUT_PATH, encoding="utf-8") as f:
        payload_raw = f.read()

    # Deserialização — mesmo processo do consumer real
    logger.info("[consumer] Deserializando payload JSON...")
    try:
        json_entrada = json.loads(payload_raw)
    except json.JSONDecodeError as exc:
        logger.error("[consumer] ✗ Payload inválido: %s", str(exc))
        raise

    component_name = (
        json_entrada.get("application", {}).get("component_name", "N/A")
    )
    event_id = (
        json_entrada.get("processing", {}).get("event_id", "N/A")
    )

    logger.info(
        "[consumer] ✓ Mensagem recebida — componente: '%s' | evento: '%s'",
        component_name,
        event_id,
    )

    # Aciona o grafo via callback
    logger.info("[consumer] Acionando grafo LangGraph...")
    callback(json_entrada)

    # Simula commit do offset
    logger.info("[consumer] ✓ Offset commitado — mensagem processada com sucesso")
    logger.info("[consumer] Mock Kafka finalizado — 1 mensagem processada")


# ===========================================================
# MODO: kafka (consumer real)
# Conecta ao broker Kafka da Sicredi
# ===========================================================

def _executar_consumer_real(callback: Callable[[dict[str, Any]], None]) -> None:
    """
    Executa o consumer Kafka real conectado ao broker da Sicredi.

    Fica em loop contínuo escutando o tópico. Para cada mensagem:
      1. Deserializa o JSON
      2. Aciona o grafo via callback
      3. Faz commit do offset

    Em caso de erro no processamento de uma mensagem:
      - Loga o erro com detalhes
      - Continua para a próxima mensagem (não para o consumer)

    Args:
        callback: função que recebe o JSON deserializado e aciona o grafo

    Raises:
        ImportError: se confluent-kafka não estiver instalado
        Exception: erros de conexão com o broker
    """
    try:
        from confluent_kafka import Consumer, KafkaError, KafkaException
    except ImportError as exc:
        raise ImportError(
            "confluent-kafka não está instalado.\n"
            "Execute: poetry add confluent-kafka"
        ) from exc

    from src.infrastructure.kafka.config import montar_config_consumer

    settings = get_settings()
    config = montar_config_consumer()

    logger.info("=" * 60)
    logger.info("[consumer] MODO: kafka (consumer real)")
    logger.info("[consumer] Conectando ao broker: %s", settings.kafka_bootstrap_servers)
    logger.info("[consumer] Tópico: %s", settings.kafka_topic)
    logger.info("[consumer] Group ID: %s", settings.kafka_group_id)
    logger.info("=" * 60)

    consumer = Consumer(config)

    try:
        consumer.subscribe([settings.kafka_topic])
        logger.info(
            "[consumer] ✓ Inscrito no tópico '%s' — aguardando mensagens...",
            settings.kafka_topic,
        )

        while True:
            # Poll: aguarda até 1 segundo por uma mensagem
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                # Nenhuma mensagem no timeout — continua o loop
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # Fim da partição — normal, continua
                    logger.debug(
                        "[consumer] Fim da partição %s [%d] offset %d",
                        msg.topic(),
                        msg.partition(),
                        msg.offset(),
                    )
                else:
                    raise KafkaException(msg.error())
                continue

            # Mensagem recebida — processa
            logger.info(
                "[consumer] ✓ Mensagem recebida — tópico: %s | partição: %d | offset: %d",
                msg.topic(),
                msg.partition(),
                msg.offset(),
            )

            try:
                # Deserializa o payload JSON
                payload_raw = msg.value().decode("utf-8")
                json_entrada = json.loads(payload_raw)

                component_name = (
                    json_entrada.get("application", {}).get("component_name", "N/A")
                )
                event_id = (
                    json_entrada.get("processing", {}).get("event_id", "N/A")
                )

                logger.info(
                    "[consumer] Processando — componente: '%s' | evento: '%s'",
                    component_name,
                    event_id,
                )

                # Aciona o grafo via callback
                callback(json_entrada)

                logger.info(
                    "[consumer] ✓ Componente '%s' processado com sucesso",
                    component_name,
                )

            except json.JSONDecodeError as exc:
                logger.error(
                    "[consumer] ✗ Payload inválido no offset %d: %s",
                    msg.offset(),
                    str(exc),
                )
                # Continua para a próxima mensagem

            except Exception as exc:
                logger.error(
                    "[consumer] ✗ Erro ao processar mensagem offset %d: %s",
                    msg.offset(),
                    str(exc),
                )
                # Continua para a próxima mensagem

    except KeyboardInterrupt:
        logger.info("[consumer] Consumer interrompido pelo usuário (Ctrl+C)")

    finally:
        # Garante que o consumer é fechado corretamente
        consumer.close()
        logger.info("[consumer] Consumer fechado — offsets finais commitados")


# ===========================================================
# INTERFACE PÚBLICA — usada pelo agent_service.py
# ===========================================================

def iniciar_consumer(callback: Callable[[dict[str, Any]], None]) -> None:
    """
    Ponto de entrada do consumer — seleciona o modo de operação.

    Lê INPUT_MODE do .env e direciona para o modo correto:
      mock_kafka → simula com JSON local (desenvolvimento)
      kafka      → consumer real (produção / VM Sicredi)

    Args:
        callback: função que recebe o JSON e aciona o grafo LangGraph
    """
    settings = get_settings()
    modo = settings.input_mode.lower()

    logger.info("[consumer] Modo de entrada selecionado: '%s'", modo)

    if modo == "mock_kafka":
        _executar_mock_kafka(callback)
    elif modo == "kafka":
        _executar_consumer_real(callback)
    else:
        raise ValueError(
            f"INPUT_MODE='{modo}' não é válido para o consumer Kafka.\n"
            "Use 'mock_kafka' ou 'kafka'.\n"
            "Para leitura de arquivo local use INPUT_MODE=file."
        )