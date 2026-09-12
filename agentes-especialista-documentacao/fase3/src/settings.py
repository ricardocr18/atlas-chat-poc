"""
settings.py
-----------
Gerenciamento centralizado de configurações da aplicação.

Utiliza pydantic-settings para carregar variáveis do arquivo .env
automaticamente, com tipagem e validação garantidas pelo Pydantic.

Padrão: qualquer parte do sistema importa `get_settings()` e nunca
acessa `os.environ` diretamente — isso mantém a configuração
rastreável e testável.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações centrais da aplicação.

    Cada campo mapeia diretamente para uma variável de ambiente.
    O Pydantic valida os tipos automaticamente na inicialização.
    """

    # --- MongoDB ---
    mongodb_uri: str
    mongodb_database: str

    # --- Aplicação ---
    app_env: str = "development"
    app_log_level: str = "INFO"

    # --- OpenAI ---
    # Chave de API da OpenAI — obrigatória na Fase 3
    # Nunca versionar este valor no git — sempre via .env
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # MONGODB_URI == mongodb_uri
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna a instância única de Settings (singleton via cache).

    O @lru_cache garante que o arquivo .env é lido apenas uma vez
    durante o ciclo de vida da aplicação, evitando leituras repetidas
    de disco a cada chamada.
    """
    return Settings()