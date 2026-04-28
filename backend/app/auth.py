"""
Authentication and authorization module for SecureVault.
Handles JWT-based authentication, password hashing, RBAC middleware,
and account lockout protection.
"""
import os
import re
import bcrypt
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.models import User, Role
from app.utils import get_db


JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key")
JWT_ALGORITHM = "HS256"

JWT_EXPIRATION_HOURS = 24
REFRESH_TOKEN_DAYS = 7

# Account lockout configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

security = HTTPBearer()


def validate_username(username: str) -> None:
    """
    Validate username requirements.
    
    Requirements:
    - Only alphanumeric characters (letters and numbers)
    - Must not start with a numeric digit
    - Minimum 3 characters, maximum 50 characters
    - No SQL injection patterns
    
    Raises HTTPException if username doesn't meet requirements.
    """
    if not username or not username.strip():
        raise HTTPException(
            status_code=400,
            detail="Username cannot be empty"
        )
    
    username = username.strip()
    
    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must be at least 3 characters long"
        )
    
    if len(username) > 50:
        raise HTTPException(
            status_code=400,
            detail="Username must be at most 50 characters long"
        )
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9]*$', username):
        raise HTTPException(
            status_code=400,
            detail="Username must start with a letter and contain only letters and numbers"
        )


def validate_password_strength(password: str) -> None:
    """
    Validate password strength requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one numeric digit
    - At least one special character
    """
    if not password:
        raise HTTPException(
            status_code=400,
            detail="Password cannot be empty"
        )
    
    if len(password) < 8:
        raise HTTPException(
            status_code=400, 
            detail="Password must be at least 8 characters long"
        )
    
    if len(password) > 128:
        raise HTTPException(
            status_code=400,
            detail="Password must be at most 128 characters long"
        )
    
    if not re.search(r'[A-Z]', password):
        raise HTTPException(
            status_code=400, 
            detail="Password must contain at least one uppercase letter"
        )
    
    if not re.search(r'[a-z]', password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one lowercase letter"
        )
    
    if not re.search(r'[0-9]', password):
        raise HTTPException(
            status_code=400, 
            detail="Password must contain at least one numeric digit"
        )
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]', password):
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least one special character"
        )


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_access_token(user_id: int, username: str, role_name: str) -> str:
    """Create a JWT access token for authenticated user."""
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role_name,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(user_id: int) -> str:
    """Create a JWT refresh token for token renewal."""
    expiration = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_DAYS)
    payload = {
        "user_id": user_id,
        "exp": expiration,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """
    Dependency function to get current authenticated user from JWT token.
    Validates token and retrieves user from database.
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


def require_permission(permission: str):
    """
    RBAC middleware decorator to check user permissions.
    Validates that the current user has the required permission.
    """
    def permission_checker(user: User = Depends(get_current_user)) -> User:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Required permission: {permission}"
            )
        return user
    return permission_checker


def check_account_lockout(user: User) -> None:
    """
    Check if a user account is currently locked out.
    
    Raises HTTPException with 423 (Locked) status if the account is locked,
    including the remaining lockout time in the error detail.
    """
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining = user.locked_until - datetime.utcnow()
        remaining_minutes = max(1, int(remaining.total_seconds() / 60))
        raise HTTPException(
            status_code=423,
            detail=f"Account is locked due to too many failed login attempts. Try again in {remaining_minutes} minute(s)."
        )


def record_failed_login(db: Session, user: User) -> None:
    """
    Record a failed login attempt and lock the account if threshold is reached.
    
    Increments failed_attempts counter. If MAX_FAILED_ATTEMPTS is reached,
    sets locked_until to current time + LOCKOUT_DURATION_MINUTES.
    """
    user.failed_attempts = (user.failed_attempts or 0) + 1
    
    if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    
    db.commit()


def reset_failed_attempts(db: Session, user: User) -> None:
    """
    Reset the failed login counter after a successful login.
    Clears both failed_attempts and locked_until fields.
    """
    if user.failed_attempts > 0 or user.locked_until is not None:
        user.failed_attempts = 0
        user.locked_until = None
        db.commit()


def register_user(db: Session, username: str, password: str, role_name: str = "Standard User") -> User:
    """Register a new user with username and password validation."""
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Get Role
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Role '{role_name}' not found")
    
    # Validate username
    validate_username(username)
    
    # Validate password strength
    validate_password_strength(password)
    
    password_hash = hash_password(password)
    new_user = User(
        username=username,
        password_hash=password_hash,
        role_id=role.role_id,
        failed_attempts=0,
        locked_until=None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate user credentials with account lockout protection.
    
    Flow:
    1. Look up user by username
    2. Check if account is locked → raise 423 if locked
    3. Verify password
    4. On failure → increment failed_attempts, potentially lock
    5. On success → reset failed_attempts counter
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Return None for non-existent users (don't reveal user existence)
        return None
    
    # Check if the account is currently locked out
    check_account_lockout(user)
    
    # Verify password
    if not verify_password(password, user.password_hash):
        # Record the failed attempt (may trigger lockout)
        record_failed_login(db, user)
        return None
    
    # Successful login — reset the counter
    reset_failed_attempts(db, user)
    return user


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
