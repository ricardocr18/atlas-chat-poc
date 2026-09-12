"""
settings.py
-----------
Gerenciamento centralizado de configurações da aplicação.

Utiliza pydantic-settings para carregar variáveis do arquivo .env
automaticamente, com tipagem e validação garantidas pelo Pydantic.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações centrais da aplicação.
    Cada campo mapeia diretamente para uma variável de ambiente.
    """

    # --- MongoDB ---
    mongodb_uri: str
    mongodb_database: str

    # --- Aplicação ---
    app_env: str = "development"
    app_log_level: str = "INFO"

    # --- OpenAI ---
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.3

    # --- Modo de entrada ---
    # file       → lê mock_input/component_event.json
    # mock_kafka → simula Kafka com JSON local
    # kafka      → consumer Kafka real
    input_mode: str = "file"

    # --- Kafka ---
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "atlas-processamento-assincrono-dados"
    kafka_group_id: str = "atlas-documentacao-agent-group"
    kafka_auto_offset_reset: str = "earliest"

    # --- PostgreSQL ---
    # Local: localhost:5432 com usuário postgres
    # Sicredi VM: atlas-documentacao-agent-pgdb.dev-sicredi.in
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = "atlas_documentacao_agente"
    postgres_user: str = "postgres"
    postgres_password: str
    postgres_sslmode: str = "prefer"
    postgres_connect_timeout: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna a instância única de Settings (singleton via cache).
    O @lru_cache garante que o .env é lido apenas uma vez.
    """
    return Settings()