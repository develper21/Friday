"""
Secret Management Module
Provides secure storage and retrieval of sensitive data like API keys
"""

import os
import base64
import logging
from pathlib import Path
from typing import Optional

try:
    import keyring
except ImportError:
    keyring = None

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security-related error"""
    pass


class SecretManager:
    """Manages secure storage and retrieval of secrets"""
    
    def __init__(self):
        if Fernet is None:
            raise ImportError("cryptography library is required for SecretManager")
        
        self.cipher = Fernet(self._get_or_create_key())
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        key_file = Path.home() / ".config" / "jean" / ".key"
        
        if key_file.exists():
            return key_file.read_bytes()
        
        # Generate new key
        key = Fernet.generate_key()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_bytes(key)
        key_file.chmod(0o600)  # Owner only
        return key
    
    def store_secret(self, name: str, value: str) -> bool:
        """Store encrypted secret"""
        try:
            encrypted = self.cipher.encrypt(value.encode())
            
            # Use system keyring if available
            if keyring:
                try:
                    keyring.set_password("jean", name, base64.b64encode(encrypted).decode())
                    return True
                except Exception as e:
                    logger.warning(f"Keyring storage failed, falling back to file: {e}")
            
            # Fallback to encrypted file
            secret_file = Path.home() / ".config" / "jean" / f"{name}.enc"
            secret_file.parent.mkdir(parents=True, exist_ok=True)
            secret_file.write_bytes(encrypted)
            secret_file.chmod(0o600)
            return True
            
        except Exception as e:
            logger.error(f"Failed to store secret: {e}")
            return False
    
    def get_secret(self, name: str) -> Optional[str]:
        """Retrieve decrypted secret"""
        try:
            encrypted = None
            
            # Try keyring first
            if keyring:
                try:
                    encrypted_b64 = keyring.get_password("jean", name)
                    if encrypted_b64:
                        encrypted = base64.b64decode(encrypted_b64)
                except Exception as e:
                    logger.debug(f"Keyring retrieval failed: {e}")
            
            # Fallback to file
            if encrypted is None:
                secret_file = Path.home() / ".config" / "jean" / f"{name}.enc"
                if secret_file.exists():
                    encrypted = secret_file.read_bytes()
                else:
                    return None
            
            decrypted = self.cipher.decrypt(encrypted)
            return decrypted.decode()
            
        except Exception as e:
            logger.error(f"Failed to retrieve secret: {e}")
            return None
    
    def delete_secret(self, name: str) -> bool:
        """Delete a secret"""
        try:
            # Try keyring
            if keyring:
                try:
                    keyring.delete_password("jean", name)
                except Exception:
                    pass
            
            # Delete file
            secret_file = Path.home() / ".config" / "jean" / f"{name}.enc"
            if secret_file.exists():
                secret_file.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete secret: {e}")
            return False
