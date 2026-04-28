"""
Utility functions for SecureVault.
Common helper functions used across the application.
Includes hardened input sanitization and validation utilities.
"""
import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base


# Module-level singleton engine to prevent connection leaks
_engine = None
_SessionLocal = None


def get_database_url() -> str:
    """Get database URL from environment variable."""
    return os.getenv("DATABASE_URL", "mysql+pymysql://admin:password@localhost:3306/SecureVault")


def _get_engine():
    """
    Get or create the global SQLAlchemy engine singleton.
    Uses connection pooling with health checks for production reliability.
    """
    global _engine, _SessionLocal
    if _engine is None:
        database_url = get_database_url()
        _engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,      # Verify connections before use
            pool_recycle=3600,        # Recycle connections after 1 hour
            pool_size=10,             # Max persistent connections
            max_overflow=20           # Extra connections under load
        )
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine, _SessionLocal


def init_database():
    """
    Initialize database connection and create all tables.
    Called at application startup.
    """
    engine, _ = _get_engine()
    Base.metadata.create_all(bind=engine)
    return engine


def get_db_session(engine):
    """Create a new database session."""
    _, SessionLocal = _get_engine()
    return SessionLocal()


def get_db():
    """
    Dependency function for FastAPI to get database session.
    Yields session and ensures cleanup after request.
    Uses singleton engine to prevent connection leaks.
    """
    _, SessionLocal = _get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===== File Size Validation =====

# Blocked file extensions (dangerous executable types)
BLOCKED_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.msi', '.scr', '.pif',
    '.ps1', '.psm1', '.vbs', '.vbe', '.js', '.jse', '.wsf',
    '.wsh', '.sh', '.csh', '.bash', '.reg'
}


def validate_file_size(file_size: int, max_size_mb: int = 100) -> bool:
    """
    Validate file size against maximum allowed size.
    Default max size is 100MB.
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and injection attacks.
    
    Protection against:
    - Directory traversal (../, ..\\)
    - Null bytes
    - Hidden files (leading dots)
    - Overly long filenames
    - Blocked executable extensions
    - Non-printable characters
    """
    if not filename:
        return "unnamed_file"
    
    # Remove null bytes
    filename = filename.replace('\x00', '')
    
    # Extract basename only (strips any path components)
    filename = os.path.basename(filename)
    
    # Remove directory traversal patterns
    filename = filename.replace("..", "")
    filename = filename.replace("/", "")
    filename = filename.replace("\\", "")
    
    # Remove non-printable characters
    filename = re.sub(r'[^\x20-\x7E]', '', filename)
    
    # Remove leading dots (hidden files) and spaces
    filename = filename.lstrip('. ')
    
    # Truncate to 255 characters max (filesystem limit)
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    
    # Check for blocked extensions
    _, ext = os.path.splitext(filename.lower())
    if ext in BLOCKED_EXTENSIONS:
        filename = filename + '.blocked'
    
    # Fallback if filename is empty after sanitization
    if not filename or not filename.strip():
        return "unnamed_file"
    
    return filename


def validate_role_name(name: str) -> str:
    """
    Validate and sanitize a role name.
    
    Requirements:
    - 2-50 characters
    - Only letters, numbers, spaces, hyphens, underscores
    - No SQL injection patterns
    """
    if not name or not name.strip():
        raise ValueError("Role name cannot be empty")
    
    name = name.strip()
    
    if len(name) < 2:
        raise ValueError("Role name must be at least 2 characters long")
    
    if len(name) > 50:
        raise ValueError("Role name must be at most 50 characters long")
    
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9 _\-]*$', name):
        raise ValueError("Role name must start with a letter and contain only letters, numbers, spaces, hyphens, and underscores")
    
    return name


def validate_permissions_list(permissions: list) -> list:
    """
    Validate a list of permission strings.
    
    Only known permission names are allowed. Prevents injection
    of arbitrary permission strings.
    """
    VALID_PERMISSIONS = {'upload', 'download', 'rename', 'delete', 'view_logs', 'manage_roles'}
    
    if not permissions:
        raise ValueError("At least one permission is required")
    
    validated = []
    for perm in permissions:
        if not isinstance(perm, str):
            raise ValueError(f"Invalid permission type: {type(perm)}")
        perm = perm.strip().lower()
        if perm not in VALID_PERMISSIONS:
            raise ValueError(f"Unknown permission: '{perm}'. Valid permissions: {', '.join(sorted(VALID_PERMISSIONS))}")
        validated.append(perm)
    
    return validated


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def get_log_level() -> str:
    """Get logging level from environment variable."""
    return os.getenv("LOG_LEVEL", "info").upper()
