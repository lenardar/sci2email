import aiosmtplib
from email.message import EmailMessage
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AppConfig


def _read_config(db: Session, key: str, default: str = "") -> str:
    row = db.query(AppConfig).filter(AppConfig.key == key).first()
    if not row:
        return default
    return row.value or default


def get_smtp_settings(db: Session) -> dict:
    host = _read_config(db, "smtp_host", settings.smtp_host)
    port = int(_read_config(db, "smtp_port", str(settings.smtp_port)))
    username = _read_config(db, "smtp_username", settings.smtp_username)
    password = _read_config(db, "smtp_password", settings.smtp_password)
    from_email = _read_config(db, "smtp_from_email", settings.smtp_from_email or settings.smtp_username)
    use_tls = _read_config(db, "smtp_use_tls", str(settings.smtp_use_tls)).lower() in ("1", "true", "yes")
    return {
        "smtp_host": host,
        "smtp_port": port,
        "smtp_username": username,
        "smtp_password": password,
        "smtp_from_email": from_email,
        "smtp_use_tls": use_tls,
    }


async def send_email(to_email: str, subject: str, html: str, smtp: dict) -> None:
    if not smtp["smtp_host"] or not smtp["smtp_username"] or not smtp["smtp_password"]:
        raise RuntimeError("SMTP is not configured")

    message = EmailMessage()
    message["From"] = smtp["smtp_from_email"] or smtp["smtp_username"]
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content("Your email client does not support HTML")
    message.add_alternative(html, subtype="html")

    await aiosmtplib.send(
        message,
        hostname=smtp["smtp_host"],
        port=smtp["smtp_port"],
        username=smtp["smtp_username"],
        password=smtp["smtp_password"],
        use_tls=smtp["smtp_use_tls"],
    )
