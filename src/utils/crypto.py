"""
Password hashing and verification for Computer Lockdown.

Uses **bcrypt** when available for strong adaptive hashing.  Falls back to
PBKDF2-HMAC-SHA256 (via :mod:`hashlib`) with a random salt when bcrypt is not
installed — this keeps the application functional during development on
machines where compiling native extensions is impractical.
"""

import hashlib
import logging
import os
import secrets
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import bcrypt; set a flag so callers can choose the right path
# ---------------------------------------------------------------------------

try:
    import bcrypt  # type: ignore[import-untyped]

    _BCRYPT_AVAILABLE: bool = True
    logger.debug("bcrypt is available — using bcrypt for password hashing.")
except ImportError:
    _BCRYPT_AVAILABLE = False
    logger.warning(
        "bcrypt is not installed — falling back to PBKDF2-HMAC-SHA256. "
        "Install bcrypt for stronger hashing: pip install bcrypt"
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PBKDF2_ITERATIONS: int = 600_000  # OWASP recommendation (2023+)
_PBKDF2_PREFIX: str = "pbkdf2:"      # tag so verify_password knows the scheme
_SALT_LENGTH: int = 32                # bytes of random salt for PBKDF2


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash *password* and return a storable string.

    Returns a bcrypt hash when the library is available, otherwise a
    ``pbkdf2:<salt_hex>:<hash_hex>`` string.

    Args:
        password: The plaintext password to hash.

    Returns:
        A string safe to persist in the configuration file.
    """
    if _BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt()
        hashed: bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    # Fallback: PBKDF2-HMAC-SHA256
    salt = os.urandom(_SALT_LENGTH)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return f"{_PBKDF2_PREFIX}{salt.hex()}:{dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Check *password* against a previously stored *hashed* value.

    Automatically detects whether the hash was created with bcrypt or the
    PBKDF2 fallback.

    Args:
        password: The plaintext password to verify.
        hashed: The stored hash string produced by :func:`hash_password`.

    Returns:
        ``True`` if the password matches, ``False`` otherwise.
    """
    if not hashed:
        return False

    try:
        if hashed.startswith(_PBKDF2_PREFIX):
            return _verify_pbkdf2(password, hashed)

        # Assume bcrypt format
        if _BCRYPT_AVAILABLE:
            return bcrypt.checkpw(
                password.encode("utf-8"),
                hashed.encode("utf-8"),
            )

        # Hash is bcrypt but the library is missing — cannot verify
        logger.error(
            "Stored hash appears to be bcrypt but bcrypt is not installed. "
            "Install bcrypt to verify this password."
        )
        return False
    except Exception as exc:
        logger.error("Password verification failed: %s", exc)
        return False


def generate_salt() -> str:
    """Return a cryptographically random hex salt string (32 bytes / 64 hex chars)."""
    return secrets.token_hex(_SALT_LENGTH)


def is_password_set(config_manager: Optional[object] = None) -> bool:
    """Return ``True`` if an admin password hash exists in the configuration.

    Args:
        config_manager: A :class:`~src.utils.config.ConfigManager` instance.
            If ``None`` a new one is created and loaded automatically.

    Returns:
        ``True`` when a non-empty ``admin_password_hash`` is stored.
    """
    if config_manager is None:
        # Lazy import to avoid circular dependency at module level
        from src.utils.config import ConfigManager

        config_manager = ConfigManager()
        config_manager.load()

    # ConfigManager exposes .get(key, default)
    pw_hash: str = config_manager.get("admin_password_hash", "")  # type: ignore[union-attr]
    return bool(pw_hash)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _verify_pbkdf2(password: str, stored: str) -> bool:
    """Verify a password against a ``pbkdf2:<salt>:<hash>`` string."""
    # Strip prefix
    payload = stored[len(_PBKDF2_PREFIX):]
    parts = payload.split(":")
    if len(parts) != 2:
        logger.error("Malformed PBKDF2 hash — expected 'pbkdf2:<salt>:<hash>'.")
        return False

    salt_hex, hash_hex = parts
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(hash_hex)

    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PBKDF2_ITERATIONS,
    )
    return secrets.compare_digest(dk, expected)
