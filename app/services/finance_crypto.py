import os
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken


def _get_master_key():
    """
    Local application encryption key.

    IMPORTANT:
    Keep SKYLA_FINANCE_ENCRYPTION_KEY private.
    It must never be committed to Git.
    """

    raw = os.environ.get("SKYLA_FINANCE_ENCRYPTION_KEY")

    if not raw:
        raise RuntimeError(
            "SKYLA_FINANCE_ENCRYPTION_KEY is not configured."
        )

    try:
        raw_bytes = base64.urlsafe_b64decode(raw.encode())
    except Exception as exc:
        raise RuntimeError(
            "Invalid SKYLA_FINANCE_ENCRYPTION_KEY."
        ) from exc

    if len(raw_bytes) != 32:
        raise RuntimeError(
            "SKYLA_FINANCE_ENCRYPTION_KEY must decode to 32 bytes."
        )

    return raw_bytes


def _fernet():
    return Fernet(
        base64.urlsafe_b64encode(_get_master_key())
    )


def encrypt_text(value):
    if value is None:
        return None

    value = str(value)

    if value == "":
        return ""

    token = _fernet().encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(value):
    if value is None:
        return None

    value = str(value)

    if value == "":
        return ""

    try:
        token = _fernet().decrypt(value.encode("utf-8"))
        return token.decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError(
            "Finance data could not be decrypted. "
            "Check SKYLA_FINANCE_ENCRYPTION_KEY."
        ) from exc


def generate_master_key():
    return base64.urlsafe_b64encode(
        os.urandom(32)
    ).decode("utf-8")
