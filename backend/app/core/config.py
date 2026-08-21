from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ### DB
    DATABASE_URL: str
    DIRECT_URL: str | None = None
    ### JWT
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    COOKIE_SECURE: bool = False
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    MAX_FAILED_LOGINS: int = 5
    LOGIN_LOCK_MINUTES: int = 15
    ### Front
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    ### 외부 API
    TMDB_API_KEY: str | None = None
    ALADIN_TTB_KEY: str | None = None
    KOBIS_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ### 배치
    CRON_SECRET: str | None = None
    REC_COOLDOWN_MINUTES: int = 60
    LLM_TIMEOUT_SECONDS: int = 30
    # 사용자당 LLM 2회. Vercel Hobby 함수 최대 60초라 한 번에 이만큼만
    CRON_USER_LIMIT: int = 5
    CRON_STALE_HOURS: int = 20  # 하루 1회 실행이라 20시간 지난 것만
    ### 수집
    MAX_CONCURRENCY: int = 4
    REQUEST_DELAY_SEC: float = 0.3


settings = Settings()
