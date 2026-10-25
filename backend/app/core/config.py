from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _BACKEND_DIR.parent


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/app.db"
    app_env: str = "local"
    cors_origins: str = "http://localhost:3000"
    llm_provider: str = "nvidia"
    llm_base_url: str = "https://integrate.api.nvidia.com/v1"
    llm_api_key: str = ""
    llm_model: str = "meta/llama-3.3-70b-instruct"
    llm_timeout_seconds: int = 45

    # Root .env first; backend/.env overrides when both exist (cwd-independent).
    model_config = SettingsConfigDict(
        env_file=(_PROJECT_ROOT / ".env", _BACKEND_DIR / ".env"),
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
