from __future__ import annotations

import base64
import hashlib

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover - handled at runtime when feature is configured
    Fernet = None  # type: ignore[assignment]

    class InvalidToken(Exception):  # type: ignore[override]
        pass


class TokenCipherError(ValueError):
    pass


class FernetTokenCipher:
    """Symmetric encryption helper for provider access/refresh token persistence."""

    def __init__(self, *, secret: str, key_version: str = "v1") -> None:
        normalized = secret.strip()
        normalized_key_version = key_version.strip()
        if not normalized:
            raise TokenCipherError("Token cipher secret is required.")
        if not normalized_key_version:
            raise TokenCipherError("Token cipher key version is required.")
        if Fernet is None:
            raise TokenCipherError("cryptography package is required for encrypted provider token persistence.")
        key = base64.urlsafe_b64encode(hashlib.sha256(normalized.encode("utf-8")).digest())
        self._fernet = Fernet(key)
        self.key_version = normalized_key_version

    def encrypt(self, plaintext: str) -> str:
        normalized = plaintext.strip()
        if not normalized:
            raise TokenCipherError("Cannot encrypt an empty token value.")
        return self._fernet.encrypt(normalized.encode("utf-8")).decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        normalized = ciphertext.strip()
        if not normalized:
            raise TokenCipherError("Cannot decrypt an empty token value.")
        try:
            return self._fernet.decrypt(normalized.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise TokenCipherError("Encrypted provider token is invalid or corrupted.") from exc
