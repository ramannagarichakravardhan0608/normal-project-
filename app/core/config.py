from functools import lru_cache

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TaskFlow Pro"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    secret_key: str = Field(default="change-this-secret-key", alias="SECRET_KEY")
    database_url: str = Field(default="sqlite:///./taskflow.db", alias="DATABASE_URL")
    access_token_expire_minutes: int = Field(default=480, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    auto_seed: bool = Field(default=True, alias="AUTO_SEED")
    admin_email: EmailStr = Field(default="admin@example.com", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="Admin@12345", alias="ADMIN_PASSWORD")
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def secure_cookies(self) -> bool:
        return self.cookie_secure or self.environment.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

