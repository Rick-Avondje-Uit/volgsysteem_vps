from __future__ import annotations
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from .exceptions import WeeztixTokenCryptoError

def _get_fernet() -> Fernet:
    key = getattr(settings, "WEEZTIX_TOKEN_ENCRYPTION_KEY", None)
    if not key:
        raise WeeztixTokenCryptoError("WEEZTIX_TOKEN_ENCRYPTION_KEY ontbreekt.")
    if isinstance(key, str):
        key = key.encode("utf-8")
    try:
        return Fernet(key)
    except (TypeError, ValueError) as exc:
        raise WeeztixTokenCryptoError("WEEZTIX_TOKEN_ENCRYPTION_KEY is ongeldig.") from exc


def encrypt_token(token: str | None) -> str:
    if not token:
        return ""
    if not isinstance(token, str):
        raise WeeztixTokenCryptoError("Het token moet tekst zijn.")
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str | None) -> str:
    if not encrypted_token:
        return ""
    if not isinstance(encrypted_token, str):
        raise WeeztixTokenCryptoError("Het versleutelde token moet tekst zijn.")
    try:
        return _get_fernet().decrypt(encrypted_token.encode()).decode()
    except InvalidToken as exc:
        raise WeeztixTokenCryptoError(
            "Token kan niet worden ontsleuteld; sleutel gewijzigd of token ongeldig."
        ) from exc
