"""
Encryption service for secure token storage.
Uses AES-256-GCM for authenticated encryption.
"""

import base64
import os
from typing import Optional

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings


class EncryptionError(Exception):
    """Raised when encryption/decryption operations fail."""
    pass


class EncryptionService:
    """
    AES-256-GCM encryption service for secure token storage.
    
    Uses authenticated encryption to ensure both confidentiality and integrity.
    The encryption key can be provided directly or derived from a password.
    """
    
    ALGORITHM = "AES-256-GCM"
    TAG_SIZE = 16  # GCM tag size in bytes
    IV_SIZE = 12   # GCM IV size in bytes (recommended for GCM)
    KEY_SIZE = 32  # AES-256 key size in bytes
    SALT_SIZE = 16  # Salt size for key derivation
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize the encryption service.
        
        Args:
            encryption_key: Base64-encoded 32-byte encryption key.
                           If not provided, uses ENCRYPTION_KEY from settings.
        """
        key_b64 = encryption_key or settings.encryption_key
        
        if key_b64:
            try:
                self._key = base64.urlsafe_b64decode(key_b64)
                if len(self._key) != self.KEY_SIZE:
                    raise EncryptionError(
                        f"Invalid key size: expected {self.KEY_SIZE} bytes, "
                        f"got {len(self._key)} bytes"
                    )
            except Exception as e:
                raise EncryptionError(f"Failed to decode encryption key: {e}")
        else:
            # Generate a key if none provided (for development)
            if settings.is_development():
                self._key = os.urandom(self.KEY_SIZE)
                print(
                    "WARNING: Using auto-generated encryption key. "
                    "Set ENCRYPTION_KEY environment variable for production."
                )
            else:
                raise EncryptionError(
                    "ENCRYPTION_KEY environment variable is required in production"
                )
    
    @classmethod
    def generate_key(cls) -> str:
        """
        Generate a new random encryption key.
        
        Returns:
            Base64-encoded 32-byte key suitable for AES-256.
        """
        key = os.urandom(cls.KEY_SIZE)
        return base64.urlsafe_b64encode(key).decode("utf-8")
    
    @classmethod
    def derive_key_from_password(cls, password: str, salt: Optional[bytes] = None) -> tuple[str, bytes]:
        """
        Derive an encryption key from a password using PBKDF2.
        
        Args:
            password: Password to derive key from.
            salt: Optional salt for key derivation. If not provided, a new one is generated.
        
        Returns:
            Tuple of (base64-encoded key, salt used for derivation).
        """
        if salt is None:
            salt = os.urandom(cls.SALT_SIZE)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=cls.KEY_SIZE,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(password.encode("utf-8"))
        return base64.urlsafe_b64encode(key).decode("utf-8"), salt
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string using AES-256-GCM.
        
        Args:
            plaintext: String to encrypt.
        
        Returns:
            Base64-encoded ciphertext containing IV, ciphertext, and tag.
        
        Raises:
            EncryptionError: If encryption fails.
        """
        if not plaintext:
            raise EncryptionError("Cannot encrypt empty plaintext")
        
        try:
            # Generate random IV
            iv = os.urandom(self.IV_SIZE)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self._key),
                modes.GCM(iv, tag_length=self.TAG_SIZE),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Encrypt
            plaintext_bytes = plaintext.encode("utf-8")
            ciphertext = encryptor.update(plaintext_bytes) + encryptor.finalize()
            
            # Combine IV, ciphertext, and tag
            combined = iv + ciphertext + encryptor.tag
            
            # Return base64 encoded
            return base64.urlsafe_b64encode(combined).decode("utf-8")
        
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")
    
    def decrypt(self, ciphertext_b64: str) -> str:
        """
        Decrypt a string encrypted with AES-256-GCM.
        
        Args:
            ciphertext_b64: Base64-encoded ciphertext from encrypt().
        
        Returns:
            Decrypted plaintext string.
        
        Raises:
            EncryptionError: If decryption fails (including authentication failure).
        """
        if not ciphertext_b64:
            raise EncryptionError("Cannot decrypt empty ciphertext")
        
        try:
            # Decode base64
            combined = base64.urlsafe_b64decode(ciphertext_b64)
            
            # Extract IV, ciphertext, and tag
            iv = combined[:self.IV_SIZE]
            tag = combined[-self.TAG_SIZE:]
            ciphertext = combined[self.IV_SIZE:-self.TAG_SIZE]
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self._key),
                modes.GCM(iv, tag, tag_length=self.TAG_SIZE),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt
            plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext_bytes.decode("utf-8")
        
        except InvalidTag:
            raise EncryptionError("Decryption failed: authentication tag verification failed")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")
    
    def rotate_key(self, new_key: bytes) -> None:
        """
        Rotate the encryption key.
        
        Note: This only updates the in-memory key. Callers are responsible
        for re-encrypting existing data.
        
        Args:
            new_key: New 32-byte key to use.
        
        Raises:
            EncryptionError: If key is invalid.
        """
        if len(new_key) != self.KEY_SIZE:
            raise EncryptionError(
                f"Invalid key size: expected {self.KEY_SIZE} bytes, "
                f"got {len(new_key)} bytes"
            )
        self._key = new_key


# Singleton instance
_encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """
    Get the singleton encryption service instance.
    
    Returns:
        EncryptionService instance.
    """
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service