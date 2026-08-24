"""
Cryptographic Hashing Strategy Service (Version 3 PBKDF2 + Pepper).
Implements IHashProvider to decouple cryptographic algorithm specifics from domain logic.
"""

import hashlib
import hmac
import os
import secrets
from typing import Optional

import config
from core.interfaces.security import IHashProvider


class Pbkdf2PepperHashProvider(IHashProvider):
    """
    Institutional PBKDF2-HMAC-SHA256 hash provider with salt and server-side secret pepper.
    Supports backward-compatible verification for legacy unpeppered digests.
    """

    def __init__(self, default_pepper: Optional[str] = None):
        self.default_pepper = default_pepper or getattr(
            config,
            "SECURITY_PEPPER_V3",
            os.environ.get(
                "ATM_SECURITY_PEPPER",
                "s3cr3t_ATM_p3pp3r_k3y_v3_98a7b6c5d4e3f210a8b9c0d1e2f3a4b5",
            ),
        )

    def generate_salt(self) -> str:
        """Generates a cryptographically secure random hexadecimal salt."""
        return secrets.token_hex(config.SALT_BYTE_LENGTH)

    def hash_pin(self, pin: str, salt: str, pepper: Optional[str] = None) -> str:
        """
        Computes a Version 3 (v3$) PBKDF2-HMAC-SHA256 hash.
        First binds the PIN with the server-side pepper via HMAC-SHA256,
        then derives the key over 100,000 PBKDF2 iterations using the per-user salt.
        """
        if not isinstance(pin, str) or not pin:
            raise ValueError("PIN must be a non-empty string.")
        if not isinstance(salt, str) or not salt:
            raise ValueError("Salt must be a non-empty string.")

        active_pepper = pepper or self.default_pepper
        peppered_digest = hmac.new(
            key=active_pepper.encode("utf-8"),
            msg=pin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()

        derived_key = hashlib.pbkdf2_hmac(
            hash_name=config.PBKDF2_HASH_NAME,
            password=peppered_digest,
            salt=salt.encode("utf-8"),
            iterations=config.PBKDF2_ITERATIONS,
        )
        return f"v3${derived_key.hex()}"

    def verify_pin(
        self, pin: str, salt: str, expected_hash: str, pepper: Optional[str] = None
    ) -> bool:
        """
        Verifies if the provided PIN matches expected_hash under the given salt and pepper.
        Uses constant-time comparison to prevent timing attacks.
        """
        if not isinstance(expected_hash, str) or not expected_hash:
            return False

        if expected_hash.startswith("v3$"):
            actual_hash = self.hash_pin(pin, salt, pepper)
            return secrets.compare_digest(actual_hash, expected_hash)
        else:
            # Legacy unpeppered PBKDF2 hash fallback
            derived_legacy = hashlib.pbkdf2_hmac(
                hash_name=config.PBKDF2_HASH_NAME,
                password=pin.encode("utf-8"),
                salt=salt.encode("utf-8"),
                iterations=config.PBKDF2_ITERATIONS,
            ).hex()
            return secrets.compare_digest(derived_legacy, expected_hash)
