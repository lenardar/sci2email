import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        salt, digest = hashed_password.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return hmac.compare_digest(digest, check)


def get_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}${digest}"


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
