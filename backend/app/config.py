from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    # Async SQLAlchemy URL (asyncpg driver).
    database_url: str = (
        "postgresql+asyncpg://romafiorita:romafiorita@localhost:5432/romafiorita"
    )
    redis_url: str = "redis://localhost:6379/0"

    # CORS: storefront + admin + localhost dev. Tighten in prod via env.
    cors_origins: list[str] = [
        "https://romafiorita.com",
        "https://admin.romafiorita.com",
        "http://localhost:3000",
    ]

    # Secrets — placeholders; set real values via env, never commit.
    jwt_secret: str = "dev-only-change-me"
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    resend_api_key: str = ""


settings = Settings()
