from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _get_fernet() -> Fernet:
    settings = get_settings()
    key_material = settings.jwt_secret_key.encode("utf-8")
    derived = hashlib.sha256(key_material).digest()
    return Fernet(base64.urlsafe_b64encode(derived))


def encrypt_value(plain: str) -> str:
    return _get_fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_value(cipher: str) -> str:
    return _get_fernet().decrypt(cipher.encode("utf-8")).decode("utf-8")
