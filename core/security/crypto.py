"""
JARVIS OS - Cryptographic Helpers
=================================

Secure, production-grade cryptography utilities.

Features:
- Key pair generation (RSA + Ed25519 options)
- Symmetric encryption (AES-GCM)
- Password hashing (Argon2id via passlib or pbkdf2 fallback)
- Secure random token generation
- Data signing / verification

Security Notes:
- Never use for long-term storage of user secrets without additional layers
- All keys are generated with secure random
- Uses modern, audited primitives where possible
- Never log keys or plaintext secrets

Dependencies:
- cryptography (already in core requirements)
- For production password hashing we use passlib[argon2] when available
"""

from __future__ import annotations

import base64
import secrets
from dataclasses import dataclass
from typing import Literal

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger

try:
    from passlib.context import CryptContext  # type: ignore

    _HAS_PASSLIB = True
except ImportError:
    _HAS_PASSLIB = False


# =============================================================================
# Constants
# =============================================================================

DEFAULT_RSA_KEY_SIZE = 2048
DEFAULT_AES_KEY_SIZE = 32  # 256-bit
PBKDF2_ITERATIONS = 600_000
SALT_SIZE = 16


# =============================================================================
# Data Models
# =============================================================================


@dataclass(frozen=True)
class KeyPair:
    """Represents an asymmetric key pair."""

    private_key: bytes
    public_key: bytes
    key_type: Literal["rsa", "ed25519"]
    fingerprint: str


@dataclass
class EncryptedData:
    """Encrypted payload with metadata."""

    ciphertext: bytes
    nonce: bytes
    tag: bytes | None = None  # For AES-GCM
    algorithm: str = "AES-256-GCM"


# =============================================================================
# Asymmetric Keys
# =============================================================================


def generate_key_pair(
    key_type: Literal["rsa", "ed25519"] = "ed25519",
    key_size: int = DEFAULT_RSA_KEY_SIZE,
) -> KeyPair:
    """
    Generate a new asymmetric key pair.

    Ed25519 is preferred for modern use cases (signing).
    RSA is available for compatibility.
    """
    if key_type == "ed25519":
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        key_type_str: Literal["rsa", "ed25519"] = "ed25519"
    else:
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )
        public_key = private_key.public_key()
        key_type_str = "rsa"

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    # Simple fingerprint (SHA256 of public key)
    digest = hashes.Hash(hashes.SHA256())
    digest.update(public_pem)
    fingerprint = base64.b64encode(digest.finalize()).decode()[:16]

    logger.debug(f"Generated {key_type_str} key pair (fingerprint: {fingerprint})")

    return KeyPair(
        private_key=private_pem,
        public_key=public_pem,
        key_type=key_type_str,
        fingerprint=fingerprint,
    )


def load_private_key(pem_data: bytes, password: bytes | None = None) -> PrivateKeyTypes:
    """Load a private key from PEM bytes."""
    return serialization.load_pem_private_key(pem_data, password=password)


# =============================================================================
# Symmetric Encryption (AES-GCM)
# =============================================================================


def generate_aes_key() -> bytes:
    """Generate a 256-bit AES key."""
    return secrets.token_bytes(DEFAULT_AES_KEY_SIZE)


def encrypt_data(plaintext: bytes | str, key: bytes) -> EncryptedData:
    """
    Encrypt data using AES-256-GCM.

    Returns an object containing ciphertext + nonce.
    """
    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")

    if len(key) != DEFAULT_AES_KEY_SIZE:
        raise ValueError("AES key must be 32 bytes (256-bit)")

    aesgcm = AESGCM(key)
    nonce = secrets.token_bytes(12)  # 96-bit nonce recommended for GCM
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    return EncryptedData(
        ciphertext=ciphertext,
        nonce=nonce,
        algorithm="AES-256-GCM",
    )


def decrypt_data(encrypted: EncryptedData, key: bytes) -> bytes:
    """Decrypt AES-GCM data."""
    if len(key) != DEFAULT_AES_KEY_SIZE:
        raise ValueError("AES key must be 32 bytes")

    aesgcm = AESGCM(key)
    try:
        return aesgcm.decrypt(encrypted.nonce, encrypted.ciphertext, None)
    except Exception as exc:
        logger.error("Decryption failed")
        raise ValueError("Decryption failed - invalid key or corrupted data") from exc


def encrypt_string(plaintext: str, key: bytes) -> str:
    """Convenience: encrypt string and return base64 encoded result."""
    enc = encrypt_data(plaintext, key)
    payload = base64.b64encode(enc.nonce + enc.ciphertext).decode()
    return payload


def decrypt_string(encrypted_b64: str, key: bytes) -> str:
    """Convenience: decrypt base64 string."""
    raw = base64.b64decode(encrypted_b64)
    nonce = raw[:12]
    ciphertext = raw[12:]
    enc = EncryptedData(ciphertext=ciphertext, nonce=nonce)
    return decrypt_data(enc, key).decode("utf-8")


# =============================================================================
# Password Hashing
# =============================================================================

if _HAS_PASSLIB:
    _pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
else:
    _pwd_context = None
    logger.warning("passlib not installed - falling back to PBKDF2 (less secure)")


def hash_password(password: str) -> str:
    """Hash a password using Argon2 (preferred) or PBKDF2 fallback."""
    if _pwd_context:
        return _pwd_context.hash(password)

    # Fallback PBKDF2
    salt = secrets.token_bytes(SALT_SIZE)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    key = kdf.derive(password.encode())
    return base64.b64encode(salt + key).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    if _pwd_context:
        try:
            return _pwd_context.verify(password, hashed)
        except Exception:
            return False

    # PBKDF2 fallback verification
    try:
        raw = base64.b64decode(hashed)
        salt = raw[:SALT_SIZE]
        stored_key = raw[SALT_SIZE:]
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=PBKDF2_ITERATIONS,
        )
        computed = kdf.derive(password.encode())
        return secrets.compare_digest(computed, stored_key)
    except Exception:
        return False


# =============================================================================
# Utilities
# =============================================================================


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(length)


def generate_fernet_key() -> str:
    """Generate a Fernet key (useful for symmetric sessions)."""
    return Fernet.generate_key().decode()


def get_fernet_cipher(key: str) -> Fernet:
    """Return a Fernet instance from base64 key."""
    return Fernet(key.encode())


__all__ = [
    "KeyPair",
    "EncryptedData",
    "generate_key_pair",
    "load_private_key",
    "generate_aes_key",
    "encrypt_data",
    "decrypt_data",
    "encrypt_string",
    "decrypt_string",
    "hash_password",
    "verify_password",
    "generate_secure_token",
    "generate_fernet_key",
]
