# Changelog

All notable changes to SecureVault will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.0.0] — 2026-04-28

### Added

- **Core Platform**
  - FastAPI REST backend with 25+ endpoints
  - Single-page frontend dashboard with client-side routing
  - MySQL 8.0 database with relational schema
  - Docker Compose multi-service orchestration

- **Authentication & Security**
  - JWT access + refresh token authentication
  - Bcrypt password hashing with salt
  - Account lockout after 5 failed login attempts (15-min cooldown)
  - Admin account unlock endpoint
  - Security headers middleware (X-Content-Type-Options, X-Frame-Options, etc.)
  - Rate limiting on auth endpoints (SlowAPI)
  - Input sanitization for filenames, usernames, and role names

- **Role-Based Access Control**
  - Three-tier role hierarchy: Admin → Manager → Standard User
  - Dynamic role creation with granular permission sets
  - Protected built-in roles (cannot be deleted)
  - Admin account immutability (cannot be deleted or demoted)
  - Per-file view/download permission grants

- **File Management**
  - Secure file upload with Fernet encryption at rest
  - File download with access control validation
  - File versioning with automatic version increment
  - Soft-delete with `is_deleted` flag for recoverability
  - SHA-256 integrity checksums
  - Filename sanitization (path traversal, null byte, extension blocking)
  - 100 MB upload size limit
  - Pluggable storage adapters (Database, Filesystem, S3 stubs)

- **Audit & Compliance**
  - Immutable audit log with SHA-256 signature per entry
  - JSON export with overall signature for tamper verification
  - CSV export for spreadsheet analysis
  - Dashboard statistics endpoint
  - Actions tracked: LOGIN, UPLOAD, DOWNLOAD, RENAME, DELETE, ROLE_UPDATE, USER_DELETE, GRANT_PERMISSION, REVOKE_PERMISSION, ACCOUNT_UNLOCK

- **Frontend Dashboard**
  - Modern dark theme with glassmorphism design
  - Inter + JetBrains Mono typography
  - Material Symbols icon integration
  - File management with upload, download, rename, delete
  - User management panel (role assignment, promotion, deletion)
  - Audit log viewer with filtering
  - Role management with custom role creation
  - Toast notification system
  - Modal confirmation dialogs

- **DevOps**
  - Multi-stage Docker builds (Python 3.11-slim, Nginx Alpine)
  - Docker Compose with health checks and service dependencies
  - Alembic migration framework configured
  - Database seeding script
  - Environment variable configuration

---

## [Unreleased]

### Planned
- Refresh token rotation
- Two-factor authentication (TOTP)
- S3 storage adapter implementation
- Filesystem storage adapter implementation
- File sharing via expiring links
- Bulk file operations
- Advanced search and filtering
- User activity dashboard
- Email notifications for security events
