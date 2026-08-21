from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "atlas_poc"
    postgres_user: str = "atlas_user"
    postgres_password: str = "atlas_pass"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "atlas_poc"
    app_env: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()