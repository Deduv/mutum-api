from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Mutum API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = (
        "Multi-tenant API for project and task management. "
        "Supports organizations, role-based access control (RBAC), "
        "member approval workflow, and platform administration."
    )
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
