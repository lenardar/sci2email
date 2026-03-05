from pydantic import BaseModel, EmailStr, Field


class RecipientIn(BaseModel):
    email: EmailStr
    enabled: bool = True


class RecipientOut(BaseModel):
    id: int
    email: EmailStr
    enabled: bool

    class Config:
        from_attributes = True


class PushTaskIn(BaseModel):
    name: str
    enabled: bool = True
    timezone: str = "Asia/Shanghai"
    send_times: list[str] = Field(default_factory=lambda: ["09:00"])
    max_items: int = 20
    source_ids: list[int] = Field(default_factory=list)
    recipient_ids: list[int] = Field(default_factory=list)


class PushTaskOut(BaseModel):
    id: int
    name: str
    enabled: bool
    timezone: str
    send_times: list[str]
    max_items: int
    source_ids: list[int]
    recipient_ids: list[int]


class SmtpSettingsIn(BaseModel):
    smtp_host: str
    smtp_port: int = 465
    smtp_username: EmailStr
    smtp_password: str = ""
    smtp_from_email: EmailStr
    smtp_use_tls: bool = True


class SmtpSettingsOut(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_from_email: str
    smtp_use_tls: bool
    has_smtp_password: bool


class AiSettingsIn(BaseModel):
    ai_enabled: bool = True
    ai_api_key: str = ""
    ai_base_url: str = "https://api.openai.com/v1"
    ai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: int = 30


class AiSettingsOut(BaseModel):
    ai_enabled: bool
    ai_base_url: str
    ai_model: str
    ai_timeout_seconds: int
    has_ai_api_key: bool
