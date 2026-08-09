from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ### DB
    DATABASE_URL: str
    DIRECT_URL: str | None = None
    ### JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ### Front
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    ### 외부 API
    TMDB_API_KEY: str | None = None
    ALADIN_TTB_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ### 배치
    CRON_SECRET: str | None = None
    REC_COOLDOWN_MINUTES: int = 60
    LLM_TIMEOUT_SECONDS: int = 30
    ### 수집
    MAX_CONCURRENCY: int = 4
    REQUEST_DELAY_SEC: float = 0.3


settings = Settings()
