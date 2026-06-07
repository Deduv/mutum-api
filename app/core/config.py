from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "DevBoard API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "API para gerenciamento de projetos e tarefas (DevBoard MVP)"
    API_V1_STR: str = "/api/v1"

    # Placeholders for future use
    DATABASE_URL: str = ""
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
