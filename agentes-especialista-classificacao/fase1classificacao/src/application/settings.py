"""Disponibiliza classe de configuracoes da aplicacao a partir do .env local.

Nota: no ambiente real da Sicredi, esta classe seria baseada em
EngineeringBaseSettings (Vault/Consul), como no scaffold oficial
atlas-classificacao-agent. Aqui, para o ambiente local mockado, usamos
pydantic-settings puro lendo de um arquivo .env — mantendo o mesmo NOME
de classe e o mesmo formato de campos, para facilitar a portabilidade
posterior para o ambiente Sicredi.
"""

from __future__ import annotations

import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuracoes da aplicacao carregadas do .env local."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Identificacao do componente
    component_name: str = Field(default="atlas-classificacao-agent")

    # --- MongoDB ---
    # Mesmo servidor do atlas-documentacao-agent, duas databases logicas:
    # uma de leitura (do agente de documentacao) e uma de escrita (propria).
    mongo_uri: str = Field(alias="MONGO_URI")
    mongo_db_documentacao: str = Field(alias="MONGO_DB_DOCUMENTACAO")
    mongo_db_classificacao: str = Field(alias="MONGO_DB_CLASSIFICACAO")

    # --- PostgreSQL ---
    # Banco compartilhado com o atlas-documentacao-agent (leitura e escrita).
    postgres_host: str = Field(alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: str = Field(default="", alias="POSTGRES_PASSWORD")
    postgres_sslmode: str = Field(default="prefer", alias="POSTGRES_SSLMODE")


# Instancia global reutilizavel, no mesmo espirito do scaffold oficial
settings: Settings | None = None
try:
    settings = Settings()
    logger.info("Configuracoes carregadas com sucesso")
except Exception as e:  # noqa: BLE001 - queremos logar qualquer erro de config
    logger.error("Erro ao carregar configuracoes: %s", e)
    raise
