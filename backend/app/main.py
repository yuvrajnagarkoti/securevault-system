"""
Main FastAPI application for SecureVault.
Provides REST API endpoints for authentication and file management.
"""
import os
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File as FastAPIFile, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from io import BytesIO

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.models import User, File, Role, FilePermission
from app.auth import (
    register_user, authenticate_user, create_access_token, 
    create_refresh_token, get_current_user, require_permission, get_client_ip
)
from app.storage import get_storage_adapter
from app.audit import log_action, get_audit_logs, export_audit_logs_json, export_audit_logs_csv, get_audit_statistics
from app.utils import get_db, init_database, sanitize_filename, validate_file_size, validate_role_name, validate_permissions_list


app = FastAPI(title="SecureVault API", version="1.0.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "http://localhost:8080",
        os.getenv("FRONTEND_URL", "http://localhost"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_database()


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class RenameRequest(BaseModel):
    new_filename: str


class RoleUpdateRequest(BaseModel):
    user_id: int
    role: str


class PermissionRequest(BaseModel):
    file_id: int
    user_id: int
    can_view: bool
    can_download: bool


class RoleCreateRequest(BaseModel):
    name: str
    permissions: list[str]



@app.post("/api/register")
@limiter.limit("5/minute")
async def register(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Register a new user with hashed password. All new users are Standard Users."""
    try:
        # All new users are registered as Standard User
        user = register_user(db, payload.username, payload.password, "Standard User")
        return {
            "status": "success",
            "message": "User registered successfully",
            "user": {
                "user_id": user.user_id,
                "username": user.username,
                "role": user.role_rel.name
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/login")
@limiter.limit("10/minute")
async def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate user and issue JWT tokens. Handles account lockout."""
    ip_address = get_client_ip(request)
    
    try:
        user = authenticate_user(db, payload.username, payload.password)
    except HTTPException as e:
        if e.status_code == 423:
            # Account is locked — log it and re-raise
            locked_user = db.query(User).filter(User.username == payload.username).first()
            if locked_user:
                log_action(db, locked_user.user_id, "LOGIN_LOCKED", None, ip_address, "Login attempt on locked account")
            raise e
        raise e
    
    if not user:
        # Log the failed attempt
        failed_user = db.query(User).filter(User.username == payload.username).first()
        if failed_user:
            log_action(db, failed_user.user_id, "LOGIN_FAILED", None, ip_address, f"Failed login attempt ({failed_user.failed_attempts} total failures)")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(user.user_id, user.username, user.role_rel.name)
    refresh_token = create_refresh_token(user.user_id)
    
    ip_address = get_client_ip(request)
    log_action(db, user.user_id, "LOGIN", None, ip_address)
    
    return {
        "status": "success",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role_rel.name
        }
    }


@app.post("/api/upload")
@limiter.limit("20/minute")
async def upload_file(
    request: Request,
    file: UploadFile = FastAPIFile(...),
    user: User = Depends(require_permission("upload")),
    db: Session = Depends(get_db)
):
    """
    Upload a file securely with permission validation.
    Stores file data and logs the action.
    """
    file_data = await file.read()
    
    if not validate_file_size(len(file_data)):
        raise HTTPException(status_code=413, detail="File too large")
    
    filename = sanitize_filename(file.filename)
    
    storage = get_storage_adapter(db)
    metadata = storage.save_file(file_data, {
        'filename': filename,
        'owner_id': user.user_id
    })
    
    ip_address = get_client_ip(request)
    log_action(db, user.user_id, "UPLOAD", metadata['file_id'], ip_address)
    
    return {
        "status": "success",
        "file": metadata
    }


@app.get("/api/files")
async def list_files(
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all files accessible to the current user (with pagination)."""
    file_list = []
    
    if user.role_rel.name in ["Admin", "Manager"]:
        # Admin and Manager can see all files
        files = db.query(File).filter(File.is_deleted == 0).limit(limit).offset(offset).all()
    else:
        # Standard User can see:
        # 1. Files they own
        own_files_query = db.query(File).filter(
            File.owner_id == user.user_id,
            File.is_deleted == 0
        )
        
        # 2. Files they have view permission for
        permissions = db.query(FilePermission).filter(
            FilePermission.user_id == user.user_id,
            FilePermission.can_view == 1
        ).all()
        
        permitted_file_ids = [p.file_id for p in permissions]
        
        if permitted_file_ids:
            permitted_files_query = db.query(File).filter(
                File.file_id.in_(permitted_file_ids),
                File.is_deleted == 0
            )
            # Combine queries with union to allow pagination
            combined_query = own_files_query.union(permitted_files_query)
        else:
            combined_query = own_files_query
            
        files = combined_query.limit(limit).offset(offset).all()
    
    for f in files:
        # Check if user has download permission
        can_download = False
        if user.role_rel.name in ["Admin", "Manager"] or f.owner_id == user.user_id:
            can_download = True
        else:
            perm = db.query(FilePermission).filter(
                FilePermission.file_id == f.file_id,
                FilePermission.user_id == user.user_id,
                FilePermission.can_download == 1
            ).first()
            can_download = perm is not None
        
        file_list.append({
            'file_id': f.file_id,
            'filename': f.filename,
            'size': f.size,
            'owner_id': f.owner_id,
            'version': f.version,
            'created_at': f.created_at.isoformat() + 'Z',
            'checksum': f.checksum,
            'can_download': can_download
        })
    
    return {
        "status": "success",
        "files": file_list
    }


@app.get("/api/download/{file_id}")
async def download_file(
    file_id: int,
    req: Request,
    user: User = Depends(require_permission("download")),
    db: Session = Depends(get_db)
):
    """
    Download a file with access control validation.
    Streams file data to client.
    """
    file_record = db.query(File).filter(
        File.file_id == file_id,
        File.is_deleted == 0
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check access permissions
    has_access = False
    
    # Admin and Manager can download any file
    if user.role_rel.name in ["Admin", "Manager"]:
        has_access = True
    # Owner can download their own files
    elif file_record.owner_id == user.user_id:
        has_access = True
    # Standard User must have download permission
    else:
        perm = db.query(FilePermission).filter(
            FilePermission.file_id == file_id,
            FilePermission.user_id == user.user_id,
            FilePermission.can_download == 1
        ).first()
        has_access = perm is not None
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied: No download permission")
    
    storage = get_storage_adapter(db)
    file_data = storage.retrieve_file(file_id)
    
    if not file_data:
        raise HTTPException(status_code=404, detail="File data not found")
    
    ip_address = get_client_ip(req)
    log_action(db, user.user_id, "DOWNLOAD", file_id, ip_address)
    
    return StreamingResponse(
        BytesIO(file_data),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file_record.filename}"}
    )


@app.put("/api/files/{file_id}/rename")
async def rename_file(
    file_id: int,
    request: RenameRequest,
    req: Request,
    user: User = Depends(require_permission("rename")),
    db: Session = Depends(get_db)
):
    """Rename file metadata (owner or Admin/Manager only)."""
    file_record = db.query(File).filter(
        File.file_id == file_id,
        File.is_deleted == 0
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if user.role_rel.name not in ["Admin", "Manager"]:
        if file_record.owner_id != user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    new_filename = sanitize_filename(request.new_filename)
    file_record.filename = new_filename
    db.commit()
    
    ip_address = get_client_ip(req)
    log_action(db, user.user_id, "RENAME", file_id, ip_address)
    
    return {
        "status": "success",
        "message": "File renamed successfully",
        "filename": new_filename
    }


@app.put("/api/files/{file_id}")
async def update_file(
    file_id: int,
    req: Request,
    file: UploadFile = FastAPIFile(...),
    user: User = Depends(require_permission("upload")),
    db: Session = Depends(get_db)
):
    """
    Upload a new version of an existing file.
    Only the owner or Admin/Manager can update a file.
    """
    file_record = db.query(File).filter(
        File.file_id == file_id,
        File.is_deleted == 0
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
        
    if user.role_rel.name not in ["Admin", "Manager"] and file_record.owner_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied: Not the owner")
        
    file_data = await file.read()
    if not validate_file_size(len(file_data)):
        raise HTTPException(status_code=413, detail="File too large")
        
    storage = get_storage_adapter(db)
    success = storage.update_file(file_id, file_data)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update file")
        
    ip_address = get_client_ip(req)
    # The file_record instance might have the updated version since session is active
    db.refresh(file_record)
    log_action(db, user.user_id, "UPDATE", file_id, ip_address, f"Updated file version to {file_record.version}")
    
    return {
        "status": "success",
        "message": "File updated successfully",
        "version": file_record.version
    }


@app.delete("/api/files/{file_id}")
async def delete_file(
    file_id: int,
    req: Request,
    user: User = Depends(require_permission("delete")),
    db: Session = Depends(get_db)
):
    """
    Soft-delete a file (owner or Admin/Manager only).
    Supports recoverability as per requirements.
    """
    file_record = db.query(File).filter(
        File.file_id == file_id,
        File.is_deleted == 0
    ).first()
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    if user.role_rel.name not in ["Admin", "Manager"]:
        if file_record.owner_id != user.user_id:
            raise HTTPException(status_code=403, detail="Access denied")
    
    storage = get_storage_adapter(db)
    storage.delete_file(file_id)
    
    ip_address = get_client_ip(req)
    log_action(db, user.user_id, "DELETE", file_id, ip_address)
    
    return {
        "status": "success",
        "message": "File deleted successfully"
    }


@app.get("/api/audit/logs")
async def get_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(require_permission("view_logs")),
    db: Session = Depends(get_db)
):
    """Retrieve audit logs (Admin/Manager only)."""
    logs = get_audit_logs(db, user_id=user_id, action=action, limit=limit, offset=offset)
    return {
        "status": "success",
        "logs": logs,
        "total": len(logs)
    }


@app.get("/api/audit/export/json")
async def export_logs_json(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    user: User = Depends(require_permission("view_logs")),
    db: Session = Depends(get_db)
):
    """Export audit logs as signed JSON snapshot."""
    json_data = export_audit_logs_json(db, user_id=user_id, action=action)
    return Response(
        content=json_data,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=audit_logs.json"}
    )


@app.get("/api/audit/export/csv")
async def export_logs_csv(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    user: User = Depends(require_permission("view_logs")),
    db: Session = Depends(get_db)
):
    """Export audit logs as CSV format."""
    csv_data = export_audit_logs_csv(db, user_id=user_id, action=action)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"}
    )


@app.get("/api/audit/statistics")
async def get_statistics(
    user: User = Depends(require_permission("view_logs")),
    db: Session = Depends(get_db)
):
    """Get audit statistics for dashboard."""
    stats = get_audit_statistics(db)
    return {
        "status": "success",
        "statistics": stats
    }


@app.get("/api/users")
async def list_users(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (Admin and Manager only)."""
    # Allow both Admin and Manager to view users
    if user.role_rel.name not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Access denied. Admin or Manager role required.")
    
    users = db.query(User).all()
    user_list = []
    for u in users:
        is_locked = bool(u.locked_until and u.locked_until > datetime.utcnow())
        user_list.append({
            'user_id': u.user_id,
            'username': u.username,
            'role': u.role_rel.name,
            'created_at': u.created_at.isoformat() + 'Z',
            'failed_attempts': u.failed_attempts or 0,
            'is_locked': is_locked,
            'locked_until': u.locked_until.isoformat() + 'Z' if u.locked_until else None
        })
    
    return {
        "status": "success",
        "users": user_list
    }


@app.put("/api/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    request: RoleUpdateRequest,
    req: Request,
    user: User = Depends(require_permission("manage_roles")),
    db: Session = Depends(get_db)
):
    """Admin can assign roles to users (Manager or Standard User only)."""
    if user_id != request.user_id:
        raise HTTPException(status_code=400, detail="User ID mismatch")
    
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from changing their own role
    if target_user.user_id == user.user_id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    # Prevent changing existing Admin users
    if target_user.role_rel.name == "Admin":
        raise HTTPException(status_code=403, detail="Cannot modify Admin accounts")
    
    new_role = db.query(Role).filter(Role.name == request.role).first()
    if not new_role:
        raise HTTPException(status_code=400, detail=f"Invalid role. Role {request.role} not found")
    
    target_user.role_id = new_role.role_id
    db.commit()
    
    ip_address = get_client_ip(req)
    log_action(db, user.user_id, "ROLE_UPDATE", None, ip_address, 
              f"Changed user {target_user.username} role to {new_role.name}")
    
    return {
        "status": "success",
        "message": f"User role updated to {new_role.name}",
        "user": {
            "user_id": target_user.user_id,
            "username": target_user.username,
            "role": target_user.role_rel.name
        }
    }


@app.delete("/api/users/{user_id}")
async def delete_user(
    user_id: int,
    req: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin can delete any user (except Admins), Manager can delete Standard Users."""
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if target_user.user_id == user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    # Prevent deleting Admin accounts
    if target_user.role_rel.name == "Admin":
        raise HTTPException(status_code=403, detail="Cannot delete Admin accounts")
    
    # Admin can delete anyone (except other Admins)
    if user.role_rel.name == "Admin":
        pass
    # Manager can only delete Standard Users
    elif user.role_rel.name == "Manager":
        if target_user.role_rel.name != "Standard User":
            raise HTTPException(status_code=403, detail="Managers can only delete Standard Users")
    else:
        raise HTTPException(status_code=403, detail="Access denied")
    
    username = target_user.username
    db.delete(target_user)
    db.commit()
    
    ip_address = get_client_ip(req)
    log_action(db, user.user_id, "USER_DELETE", None, ip_address, f"Deleted user {username}")
    
    return {
        "status": "success",
        "message": f"User {username} deleted successfully"
    }


@app.put("/api/users/{user_id}/promote")
async def promote_user(
    user_id: int,
    req: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manager can promote a Standard User to Manager."""
    if user.role_rel.name not in ["Manager", "Admin"]:
        raise HTTPException(status_code=403, detail="Only Managers and Admins can promote users")
    
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if target_user.role_rel.name != "Standard User":
        raise HTTPException(status_code=400, detail="Can only promote Standard Users")
    
    manager_role = db.query(Role).filter(Role.name == "Manager").first()
    target_user.role_id = manager_role.role_id
    db.commit()
    
    ip_address = get_client_ip(req)
    log_action(db, user.user_id, "USER_PROMOTE", None, ip_address, 
              f"Promoted user {target_user.username} to Manager")
    
    return {
        "status": "success",
        "message": f"User {target_user.username} promoted to Manager",
        "user": {
            "user_id": target_user.user_id,
            "username": target_user.username,
            "role": target_user.role_rel.name
        }
    }


@app.post("/api/files/permissions")
async def grant_file_permission(
    request: PermissionRequest,
    req: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manager grants file access to Standard Users."""
    if user.role_rel.name not in ["Manager", "Admin"]:
        raise HTTPException(status_code=403, detail="Only Managers and Admins can grant permissions")
    
    file_record = db.query(File).filter(File.file_id == request.file_id, File.is_deleted == 0).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    target_user = db.query(User).filter(User.user_id == request.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if permission already exists
    existing_perm = db.query(FilePermission).filter(
        FilePermission.file_id == request.file_id,
        FilePermission.user_id == request.user_id
    ).first()
    
    if existing_perm:
        # Update existing permission
        existing_perm.can_view = 1 if request.can_view else 0
        existing_perm.can_download = 1 if request.can_download else 0
        existing_perm.granted_by = user.user_id
        existing_perm.granted_at = datetime.utcnow()
    else:
        # Create new permission
        new_perm = FilePermission(
            file_id=request.file_id,
            user_id=request.user_id,
            can_view=1 if request.can_view else 0,
            can_download=1 if request.can_download else 0,
            granted_by=user.user_id
        )
        db.add(new_perm)
    
    db.commit()
    
    ip_address = get_client_ip(req)
    log_action(db, user.user_id, "GRANT_PERMISSION", request.file_id, ip_address,
              f"Granted permissions to user {target_user.username}")
    
    return {
        "status": "success",
        "message": "File permissions updated successfully"
    }


@app.delete("/api/files/permissions/{file_id}/{user_id}")
async def revoke_file_permission(
    file_id: int,
    user_id: int,
    req: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manager revokes file access from Standard Users."""
    if user.role_rel.name not in ["Manager", "Admin"]:
        raise HTTPException(status_code=403, detail="Only Managers and Admins can revoke permissions")
    
    permission = db.query(FilePermission).filter(
        FilePermission.file_id == file_id,
        FilePermission.user_id == user_id
    ).first()
    
    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    db.delete(permission)
    db.commit()
    
    ip_address = get_client_ip(req)
    log_action(db, user.user_id, "REVOKE_PERMISSION", file_id, ip_address,
              f"Revoked permissions from user ID {user_id}")
    
    return {
        "status": "success",
        "message": "File permissions revoked successfully"
    }


@app.get("/api/files/permissions/{file_id}")
async def get_file_permissions(
    file_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all permissions for a specific file (Manager/Admin only)."""
    if user.role_rel.name not in ["Manager", "Admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    permissions = db.query(FilePermission).filter(FilePermission.file_id == file_id).all()
    
    perm_list = []
    for perm in permissions:
        target_user = db.query(User).filter(User.user_id == perm.user_id).first()
        if target_user:
            perm_list.append({
                'user_id': perm.user_id,
                'username': target_user.username,
                'can_view': bool(perm.can_view),
                'can_download': bool(perm.can_download),
                'granted_at': perm.granted_at.isoformat() + 'Z'
            })
    
    return {
        "status": "success",
        "permissions": perm_list
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "SecureVault API"
    }


@app.get("/api/roles")
async def list_roles(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all dynamic roles."""
    if user.role_rel.name not in ["Manager", "Admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    roles = db.query(Role).all()
    return {"status": "success", "roles": [{"id": r.role_id, "name": r.name, "permissions": r.permissions} for r in roles]}


@app.post("/api/roles")
@limiter.limit("10/minute")
async def create_role(payload: RoleCreateRequest, request: Request, user: User = Depends(require_permission("manage_roles")), db: Session = Depends(get_db)):
    """Create a new dynamic role with validated inputs."""
    try:
        validated_name = validate_role_name(payload.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        validated_perms = validate_permissions_list(payload.permissions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    existing = db.query(Role).filter(Role.name == validated_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")
        
    new_role = Role(name=validated_name, permissions=validated_perms)
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return {"status": "success", "message": "Role created", "role": {"id": new_role.role_id, "name": new_role.name, "permissions": new_role.permissions}}


@app.delete("/api/roles/{role_id}")
async def delete_role(role_id: int, user: User = Depends(require_permission("manage_roles")), db: Session = Depends(get_db)):
    """Delete a dynamic role. Protected roles cannot be deleted."""
    role = db.query(Role).filter(Role.role_id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    protected = ["Admin", "Manager", "Standard User"]
    if role.name in protected:
        raise HTTPException(status_code=403, detail=f"Cannot delete protected role '{role.name}'")
    
    # Check if any users are assigned this role
    users_with_role = db.query(User).filter(User.role_id == role_id).count()
    if users_with_role > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete role '{role.name}': {users_with_role} user(s) still assigned")
    
    db.delete(role)
    db.commit()
    return {"status": "success", "message": f"Role '{role.name}' deleted"}

@app.put("/api/users/{user_id}/unlock")
async def unlock_user_account(
    user_id: int,
    req: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Admin can unlock a locked user account."""
    if user.role_rel.name != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can unlock accounts")
    
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    target_user.failed_attempts = 0
    target_user.locked_until = None
    db.commit()
    
    ip_address = get_client_ip(req)
    log_action(db, user.user_id, "ACCOUNT_UNLOCK", None, ip_address,
              f"Unlocked account for user {target_user.username}")
    
    return {
        "status": "success",
        "message": f"Account for {target_user.username} has been unlocked"
    }


@app.get("/api/users/lockout-status")
async def get_lockout_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get lockout status of all users (Admin only)."""
    if user.role_rel.name != "Admin":
        raise HTTPException(status_code=403, detail="Only Admins can view lockout status")
    
    users = db.query(User).all()
    statuses = []
    for u in users:
        is_locked = bool(u.locked_until and u.locked_until > datetime.utcnow())
        statuses.append({
            "user_id": u.user_id,
            "username": u.username,
            "failed_attempts": u.failed_attempts or 0,
            "is_locked": is_locked,
            "locked_until": u.locked_until.isoformat() + "Z" if u.locked_until else None
        })
    
    return {
        "status": "success",
        "lockout_data": statuses
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
