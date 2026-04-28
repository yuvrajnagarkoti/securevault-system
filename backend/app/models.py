"""
Database models for SecureVault system.
Defines User, File, and AuditLog tables with relationships.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime, LargeBinary, Text, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, deferred
from datetime import datetime
from sqlalchemy import JSON

Base = declarative_base()


class Role(Base):
    """Dynamic roles with custom policies."""
    __tablename__ = 'roles'
    
    role_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    permissions = Column(JSON, nullable=False)
    
    users = relationship("User", back_populates="role_rel")


class User(Base):
    """User table with authentication and role information."""
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.role_id'), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    failed_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(TIMESTAMP, nullable=True, default=None)
    
    files = relationship("File", back_populates="owner")
    audit_logs = relationship("AuditLog", back_populates="user")
    role_rel = relationship("Role", back_populates="users")
    
    def has_permission(self, action):
        """Check if user has permission for a specific action."""
        if not self.role_rel:
            return False
        
        perms = self.role_rel.permissions
        if isinstance(perms, dict):
            return bool(perms.get(action, False))
        elif isinstance(perms, list):
            return action in perms
        return False


class File(Base):
    """File table with metadata and binary storage."""
    __tablename__ = 'files'
    
    file_id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    size = Column(Integer, nullable=False)
    owner_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    checksum = Column(String(64), nullable=False)
    file_data = deferred(Column(LargeBinary, nullable=True))
    is_deleted = Column(Integer, nullable=False, default=0)
    
    owner = relationship("User", back_populates="files")
    audit_logs = relationship("AuditLog", back_populates="file")
    permissions = relationship("FilePermission", back_populates="file")


class FilePermission(Base):
    """File permission table for granular access control."""
    __tablename__ = 'file_permissions'
    
    permission_id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('files.file_id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    can_view = Column(Integer, nullable=False, default=0)
    can_download = Column(Integer, nullable=False, default=0)
    granted_by = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    granted_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    
    file = relationship("File", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by])


class AuditLog(Base):
    """Immutable audit log table for tracking all file operations."""
    __tablename__ = 'audit_logs'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    file_id = Column(Integer, ForeignKey('files.file_id'), nullable=True)
    action = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    details = Column(Text, nullable=True)
    signature_hash = Column(String(64), nullable=False)
    
    user = relationship("User", back_populates="audit_logs")
    file = relationship("File", back_populates="audit_logs")
