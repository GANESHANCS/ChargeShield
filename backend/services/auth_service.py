"""
Authentication & Authorization Service for ChargeShield.
Provides password hashing via direct bcrypt, JWT access token generation/verification,
and session token revocation tracking.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Set
import jwt
import bcrypt
from backend.core.config import settings
from backend.core.logging import logger

# In-memory token blacklist for session logout invalidation
_token_blacklist: Set[str] = set()

def hash_password(password: str) -> str:
    """Securely hashes a plaintext password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Generates a signed JWT access token containing claims: sub (user_id), email, username, role.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "iss": "chargeshield-auth"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a JWT access token.
    Returns payload dictionary or None if invalid/expired/blacklisted.
    """
    if is_token_blacklisted(token):
        logger.warning("Attempted use of blacklisted/logged-out JWT token.")
        return None

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.info("JWT token signature expired.")
        return None
    except jwt.PyJWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        return None

def revoke_token(token: str) -> None:
    """Adds a JWT token to the session revocation blacklist."""
    _token_blacklist.add(token)

def is_token_blacklisted(token: str) -> bool:
    """Checks if a JWT token has been invalidated by logout."""
    return token in _token_blacklist
