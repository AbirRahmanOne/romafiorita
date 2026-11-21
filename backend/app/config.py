from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_JWT_SECRET = "dev-only-change-me"


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
    jwt_secret: str = DEFAULT_JWT_SECRET
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    resend_api_key: str = ""

    # Auth / cookies.
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 14
    # None in dev → host-only cookies; prod sets ".romafiorita.com".
    cookie_domain: str | None = None
    login_max_attempts: int = 5
    login_lockout_minutes: int = 15
    # Reject bodies larger than this (bytes). Bouquet photos go via R2, not here.
    max_request_bytes: int = 1_000_000

    # Public storefront base for pay links / QR codes.
    pay_base_url: str = "https://romafiorita.com/pay"

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"

    @property
    def secure_cookies(self) -> bool:
        """Secure flag off in dev so the http test/dev client keeps cookies."""
        return not self.is_dev

    @model_validator(mode="after")
    def _require_real_secrets_outside_dev(self) -> "Settings":
        """Fail fast at startup if prod is running on placeholder secrets."""
        if not self.is_dev and self.jwt_secret in ("", DEFAULT_JWT_SECRET):
            raise ValueError(
                "JWT_SECRET must be set to a real value outside development."
            )
        return self


settings = Settings()
