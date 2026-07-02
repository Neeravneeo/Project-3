"""Application configuration via pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── App ──────────────────────────────────────────────────
    app_env: str = "development"
    app_secret_key: str = "change-me"
    debug: bool = True
    frontend_url: str = "http://localhost:3000"

    # ─── Database ─────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://trading_user:changeme@localhost:5432/trading"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "trading"
    postgres_user: str = "trading_user"
    postgres_password: str = "changeme"

    # ─── Redis ────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ─── Celery ───────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ─── Alpaca (US Broker) ───────────────────────────────────
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_paper: bool = True

    # ─── Zerodha Kite (India Broker) ──────────────────────────
    kite_api_key: str = ""
    kite_api_secret: str = ""
    kite_access_token: str = ""

    # ─── AI / LLM ─────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    openai_api_key: str = ""

    # ─── LangSmith ────────────────────────────────────────────
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "trading-platform"

    # ─── JWT ──────────────────────────────────────────────────
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440

    # ─── Risk Defaults ────────────────────────────────────────
    max_drawdown_trigger: float = 0.05
    max_position_beta: float = 0.90
    single_position_loss_trigger: float = 0.03
    vix_caution_level: float = 20.0
    vix_hedge_level: float = 25.0
    vix_aggressive_level: float = 30.0
    max_position_weight: float = 0.10

    # ─── Celery Beat ──────────────────────────────────────────
    market_data_refresh_interval: int = 60
    signal_generation_interval: int = 300
    risk_monitoring_interval: int = 60

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def alpaca_base_url(self) -> str:
        if self.alpaca_paper:
            return "https://paper-api.alpaca.markets"
        return "https://api.alpaca.markets"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
