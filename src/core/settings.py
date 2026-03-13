from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API
    API_ENV: str = "development"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = ""
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    DATABASE_URL: str = ""

    # LLM
    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.1
    GROQ_API_KEY: str | None = None

    # MCP
    MCP_TRANSPORT: str = "stdio"

    # CORS
    ALLOWED_ORIGINS: str = "*"

    # Auth
    AUTH_SECRET_KEY: str = "fitness-gen-dev-secret-change-me"
    AUTH_TOKEN_EXPIRES_MINUTES: int = 480

    @property
    def project_root(self) -> Path:
        return ENV_PATH.parent

    @property
    def cors_origins(self) -> list[str]:
        allowed = (self.ALLOWED_ORIGINS or "*").strip()
        if allowed == "*" or allowed.lower() == "all":
            return ["*"]
        return [origin.strip() for origin in allowed.split(",") if origin.strip()]

    @property
    def has_groq_api_key(self) -> bool:
        return bool(self.GROQ_API_KEY)

    @property
    def environment(self) -> str:
        return self.API_ENV


settings = Settings()
