from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "sci2email"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    admin_username: str = "admin"
    admin_password: str = "admin123"

    sqlite_url: str = "sqlite:///./data.db"

    smtp_host: str = "smtp.163.com"
    smtp_port: int = 465
    smtp_username: str = "your_email@163.com"
    smtp_password: str = ""
    smtp_from_email: str = "your_email@163.com"
    smtp_use_tls: bool = True

    ai_enabled: bool = True
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
