from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://claim360:claim360@localhost:5432/claim360"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    jwt_secret: str = ""
    portal_api_key: str = ""
    specialist_email: str = "specialist@local"
    specialist_password: str = ""
    llm_enabled: bool = True
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    prompt_version: int = 1
    fraud_high_threshold: int = 80
    fraud_medium_threshold: int = 50
    agent_max_retries: int = 3


def get_settings() -> Settings:
    return Settings()
