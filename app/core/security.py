import hashlib
import secrets
from datetime import datetime, timedelta, UTC
from typing import Dict
from jose import jwt
from app.core.config import settings


def create_access_token(subject: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRES_MINUTES)
    to_encode: Dict[str, str] = {"sub": subject, "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def generate_api_key() -> tuple[str, str]:
    """
    Returns (plain_key, key_hash)
    """
    plain = "sk_live_" + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(plain.encode("utf-8")).hexdigest()
    return plain, key_hash


def hash_api_key(plain_key: str) -> str:
    return hashlib.sha256(plain_key.encode("utf-8")).hexdigest()