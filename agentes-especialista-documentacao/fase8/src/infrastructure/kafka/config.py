"""
infrastructure/kafka/config.py
--------------------------------
Configurações do consumer Kafka.

Centraliza todos os parâmetros de conexão com o broker Kafka.
Quando tivermos acesso ao broker da Sicredi, apenas as variáveis
no .env precisarão ser atualizadas — este arquivo não muda.

Modos de operação (controlado por INPUT_MODE no .env):
  file        → lê o component_event.json diretamente (Fases 1-3)
  mock_kafka  → simula o Kafka usando o JSON local, mas passa
                pelo mesmo código do consumer (testa a interface)
  kafka       → consumer Kafka real (quando tivermos acesso ao broker)

Configurações que precisarão ser preenchidas quando tivermos
acesso ao broker da Sicredi:
  KAFKA_BOOTSTRAP_SERVERS → endereço do broker (ex: kafka.sicredi.net:9092)
  KAFKA_SECURITY_PROTOCOL → PLAINTEXT | SSL | SASL_SSL
  KAFKA_SASL_MECHANISM    → PLAIN | SCRAM-SHA-256 | GSSAPI (se SASL)
  KAFKA_SASL_USERNAME     → usuário (se SASL)
  KAFKA_SASL_PASSWORD     → senha (se SASL)
  KAFKA_SSL_CA_LOCATION   → caminho do certificado CA (se SSL)
"""

from src.settings import get_settings


def montar_config_consumer() -> dict:
    """
    Monta o dicionário de configuração do consumer Kafka.

    Retorna configuração completa baseada nas variáveis do .env.
    O confluent-kafka aceita este formato diretamente.

    Returns:
        dict com configurações do consumer pronto para uso
    """
    settings = get_settings()

    # --- Configuração base (sempre presente) ---
    config = {
        "bootstrap.servers": settings.kafka_bootstrap_servers,
        "group.id": settings.kafka_group_id,
        "auto.offset.reset": settings.kafka_auto_offset_reset,
        "enable.auto.commit": True,
        "session.timeout.ms": 30000,
        "max.poll.interval.ms": 300000,
    }

    # --- SSL/TLS (quando habilitado na Sicredi) ---
    # Descomente e preencha quando tiver acesso ao broker:
    #
    # if settings.kafka_security_protocol in ("SSL", "SASL_SSL"):
    #     config["security.protocol"] = settings.kafka_security_protocol
    #     config["ssl.ca.location"] = settings.kafka_ssl_ca_location
    #
    # --- SASL (quando habilitado na Sicredi) ---
    # if settings.kafka_security_protocol in ("SASL_PLAINTEXT", "SASL_SSL"):
    #     config["sasl.mechanism"] = settings.kafka_sasl_mechanism
    #     config["sasl.username"] = settings.kafka_sasl_username
    #     config["sasl.password"] = settings.kafka_sasl_password

    return config