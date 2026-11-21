import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_placeholder_secret() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="production", jwt_secret="dev-only-change-me")


def test_production_accepts_real_secret() -> None:
    s = Settings(environment="production", jwt_secret="x" * 40)
    assert s.secure_cookies is True


def test_dev_allows_placeholder_and_insecure_cookies() -> None:
    s = Settings(environment="development")
    assert s.secure_cookies is False
