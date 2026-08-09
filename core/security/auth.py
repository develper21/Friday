"""
Authentication Module
Provides JWT-based authentication for API endpoints
"""

import hashlib
import base64
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

try:
    import jwt
except ImportError:
    jwt = None

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Security-related error"""
    pass


class AuthManager:
    """Manages authentication using JWT tokens"""
    
    def __init__(self, secret_key: Optional[str] = None):
        if jwt is None:
            raise ImportError("PyJWT library is required for AuthManager")
        
        if secret_key is None:
            # Generate a secure secret key
            secret_key = base64.b64encode(os.urandom(32)).decode()
        
        self.secret_key = secret_key
        self.tokens = {}  # In production, use Redis
    
    def hash_password(self, password: str) -> str:
        """Hash password with salt using PBKDF2"""
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt,
            100000
        )
        return base64.b64encode(salt + key).decode()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            decoded = base64.b64decode(hashed)
            salt = decoded[:32]
            stored_key = decoded[32:]
            
            new_key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode(),
                salt,
                100000
            )
            
            return new_key == stored_key
        except Exception:
            return False
    
    def generate_token(self, user_id: str, expires_hours: int = 24) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['user_id']
        except jwt.ExpiredSignatureError:
            raise SecurityError("Token expired")
        except jwt.InvalidTokenError:
            raise SecurityError("Invalid token")
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token (add to blacklist)"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            token_id = payload.get('user_id', 'unknown')
            self.tokens[token] = datetime.utcnow()
            return True
        except Exception:
            return False


def require_auth(auth_manager: AuthManager):
    """Decorator for requiring authentication on endpoints"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # This is a placeholder - in a real framework like Flask/FastAPI,
            # you would extract the token from request headers
            token = kwargs.pop('auth_token', None)
            
            if not token:
                raise SecurityError("No token provided")
            
            user_id = auth_manager.verify_token(token)
            if not user_id:
                raise SecurityError("Invalid token")
            
            return func(*args, user_id=user_id, **kwargs)
        return wrapper
    return decorator
