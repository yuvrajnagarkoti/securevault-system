<p align="center">
  <img src="https://img.shields.io/badge/SecureVault-Enterprise%20File%20Management-blueviolet?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMNCA1djYuMDljMCA1LjA1IDMuNDEgOS43NiA4IDEwLjkxIDQuNTktMS4xNSA4LTUuODYgOC0xMC45MVY1bC04LTN6bTAgMTcuOTNjLTMuNzItMS4xLTYtNS4wNy02LTkuMDRWNi4zMWw2LTIuMjUgNiAyLjI1djYuNThjMCAzLjk3LTIuMjggNy45NC02IDkuMDR6IiBmaWxsPSJ3aGl0ZSIvPjwvc3ZnPg==" alt="SecureVault"/>
</p>

<h1 align="center">🛡️ SecureVault</h1>

<p align="center">
  <strong>Enterprise-Grade Secure File Management System</strong>
</p>

<p align="center">
  <a href="#-features"><img src="https://img.shields.io/badge/Features-✨-blue?style=flat-square" alt="Features"/></a>
  <a href="#-quick-start"><img src="https://img.shields.io/badge/Quick_Start-🚀-green?style=flat-square" alt="Quick Start"/></a>
  <a href="#-api-reference"><img src="https://img.shields.io/badge/API_Docs-📖-orange?style=flat-square" alt="API Docs"/></a>
  <a href="#-architecture"><img src="https://img.shields.io/badge/Architecture-🏗️-purple?style=flat-square" alt="Architecture"/></a>
  <a href="CODE_OF_CONDUCT.md"><img src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg?style=flat-square" alt="Code of Conduct"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11"/>
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white" alt="MySQL"/>
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License"/>
</p>

---

<p align="center">
  <img src="assets/dashboard_preview.png" alt="SecureVault Dashboard Preview" width="800" style="border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);"/>
</p>

---

<p align="center">
  A production-ready, containerized file management platform with <strong>dynamic role-based access control (RBAC)</strong>, <strong>AES-256 encryption at rest</strong>, <strong>immutable audit trails</strong>, and a modern single-page dashboard — all deployable with a single <code>docker compose up</code>.
</p>

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Security](#-security)
- [Role-Based Access Control](#-role-based-access-control)
- [Configuration](#-configuration)
- [Development](#-development)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🔐 Security First
- **Encryption at Rest** — All files encrypted with Fernet (AES-128-CBC) before storage
- **Bcrypt Password Hashing** — Industry-standard salted password hashing
- **JWT Authentication** — Stateless access + refresh token flow with configurable expiration
- **Account Lockout** — Automatic lockout after 5 failed login attempts (15-min cooldown)
- **Security Headers** — X-Content-Type-Options, X-Frame-Options, XSS-Protection, Referrer-Policy
- **Rate Limiting** — Endpoint-specific rate limits to prevent brute-force attacks
- **Input Sanitization** — Path traversal protection, blocked executable uploads, SQL injection prevention

### 👥 Dynamic RBAC
- **Three-tier hierarchy** — Admin → Manager → Standard User
- **Custom Roles** — Create roles with granular permission sets at runtime
- **Per-file Permissions** — Grant view/download access to individual users per file
- **Protected Roles** — Built-in roles cannot be deleted; Admin accounts are immutable

### 📁 File Management
- **Upload & Download** — Secure file transfer with SHA-256 integrity checksums
- **File Versioning** — Automatic version increment on file updates
- **Soft Delete** — Recoverable file deletion (marks `is_deleted` flag)
- **Filename Sanitization** — Strips traversal attacks, blocks dangerous extensions (`.exe`, `.bat`, `.ps1`, etc.)
- **100 MB Upload Limit** — Configurable max file size

### 📊 Audit & Compliance
- **Immutable Audit Logs** — Every action logged with SHA-256 signature hash for tamper detection
- **Export Formats** — JSON (signed snapshot) and CSV export for compliance reporting
- **Dashboard Statistics** — Real-time action counts and activity summaries
- **Full Traceability** — User, action, file, IP address, and timestamp on every entry

### 🎨 Modern Dashboard
- **Single-Page Application** — Vanilla JS with client-side routing (no framework overhead)
- **Dark Theme** — Premium glassmorphism design with Inter + JetBrains Mono typography
- **Responsive Layout** — Adaptive UI for desktop and tablet form factors
- **Real-time Feedback** — Toast notifications, modal confirmations, loading states

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                           │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────┐    ┌───────────────┐ │
│  │   Frontend    │    │    Backend API    │    │    MySQL 8    │ │
│  │  (Nginx:80)   │───▶│  (FastAPI:8000)   │───▶│   (:3306)     │ │
│  │              │    │                  │    │               │ │
│  │  index.html  │    │  /api/register   │    │  users        │ │
│  │  index.js    │    │  /api/login      │    │  files        │ │
│  │  styles/     │    │  /api/files      │    │  roles        │ │
│  │              │    │  /api/audit      │    │  audit_logs   │ │
│  │              │    │  /api/users      │    │  file_perms   │ │
│  │              │    │  /api/roles      │    │               │ │
│  └──────────────┘    └──────────────────┘    └───────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User → Nginx (port 80) → Static SPA
SPA  → FastAPI (port 8000) → JWT Validation → RBAC Check → Business Logic
Business Logic → SQLAlchemy ORM → MySQL 8.0
File Upload → Sanitize → Encrypt (Fernet) → Store as LONGBLOB
File Download → Decrypt → Stream to client
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML5 / Vanilla JS / CSS3 | Single-page application with client-side routing |
| **Web Server** | Nginx Alpine | Static file serving, reverse proxy ready |
| **Backend** | FastAPI 0.109 | Async REST API framework |
| **ORM** | SQLAlchemy 2.0 | Database abstraction + migrations |
| **Database** | MySQL 8.0 | Relational data storage |
| **Auth** | PyJWT + Bcrypt | JWT tokens + password hashing |
| **Encryption** | Cryptography (Fernet) | File encryption at rest |
| **Rate Limiting** | SlowAPI | Request throttling |
| **Migrations** | Alembic 1.13 | Schema version control |
| **Container** | Docker Compose | Multi-service orchestration |

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) installed
- Ports `80`, `8000`, and `3306` available

### One-Command Deploy

```bash
# Clone the repository
git clone https://github.com/yuvrajnagarkoti/securevault-system.git
cd securevault-system

# Copy environment config
cp .env.example .env

# Launch all services
docker compose up --build -d
```

### Access the Application

| Service | URL |
|---------|-----|
| 🌐 Dashboard | [http://localhost](http://localhost) |
| 🔌 API Docs | [http://localhost:8000/docs](http://localhost:8000/docs) |
| ❤️ Health Check | [http://localhost:8000/api/health](http://localhost:8000/api/health) |

### Default Admin Credentials

| Username | Password | Role |
|----------|----------|------|
| `Yuvraj` | `Password123##` | Admin |

> ⚠️ **Change the default password immediately in production.**

---

## 📂 Project Structure

```
SecureVault/
├── assets/
│   └── dashboard_preview.png    # High-fidelity dashboard mockup
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Package init
│   │   ├── main.py              # FastAPI app & all REST endpoints
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   ├── auth.py              # JWT auth, password hashing, RBAC middleware
│   │   ├── storage.py           # Pluggable storage adapters (DB, FS, S3)
│   │   ├── audit.py             # Immutable audit logging & export
│   │   └── utils.py             # DB init, sanitization, validation helpers
│   ├── alembic/                 # Database migration scripts
│   ├── alembic.ini              # Alembic configuration
│   ├── seed.py                  # Database seeding script
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile               # Backend container image
├── frontend/
│   ├── index.html               # SPA entry point
│   ├── index.js                 # Application logic & client-side router
│   ├── styles/
│   │   └── main.css             # Design system & component styles
│   ├── nginx.conf               # Nginx configuration (no-cache dev mode)
│   └── Dockerfile               # Frontend container image
├── database/
│   └── init.sql                 # Schema bootstrap + default data
├── .github/
│   ├── workflows/
│   │   └── ci.yml               # GitHub Actions CI workflow
│   ├── ISSUE_TEMPLATE/          # Bug & Feature templates
│   └── PULL_REQUEST_TEMPLATE.md # PR template
├── docker-compose.yml           # Multi-service orchestration
├── .env.example                 # Environment variable template
├── .gitignore                   # Git exclusion rules
├── .editorconfig                # Consistent editor formatting
├── .dockerignore                # Docker build exclusions
├── LICENSE                      # MIT License
├── CONTRIBUTING.md              # Contribution guidelines
├── CODE_OF_CONDUCT.md           # Community standards
├── SECURITY.md                  # Security policy & disclosure
├── CHANGELOG.md                 # Version history
└── README.md                    # This file
```

---

## 📖 API Reference

### Authentication

| Method | Endpoint | Description | Rate Limit |
|--------|----------|-------------|------------|
| `POST` | `/api/register` | Create new Standard User account | 5/min |
| `POST` | `/api/login` | Authenticate and receive JWT tokens | 10/min |

### File Operations

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| `GET` | `/api/files` | List accessible files (paginated) | Authenticated |
| `POST` | `/api/upload` | Upload a new file | `upload` |
| `GET` | `/api/download/{file_id}` | Download a file | `download` + access |
| `PUT` | `/api/files/{file_id}/rename` | Rename a file | `rename` + ownership |
| `PUT` | `/api/files/{file_id}` | Upload new version of file | `upload` + ownership |
| `DELETE` | `/api/files/{file_id}` | Soft-delete a file | `delete` + ownership |

### File Permissions

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| `POST` | `/api/files/permissions` | Grant view/download access | Manager/Admin |
| `GET` | `/api/files/permissions/{file_id}` | List file permissions | Manager/Admin |
| `DELETE` | `/api/files/permissions/{file_id}/{user_id}` | Revoke access | Manager/Admin |

### User Management

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| `GET` | `/api/users` | List all users | Manager/Admin |
| `PUT` | `/api/users/{user_id}/role` | Change user role | `manage_roles` |
| `PUT` | `/api/users/{user_id}/promote` | Promote to Manager | Manager/Admin |
| `DELETE` | `/api/users/{user_id}` | Delete a user | Scoped by role |
| `PUT` | `/api/users/{user_id}/unlock` | Unlock locked account | Admin |
| `GET` | `/api/users/lockout-status` | View all lockout statuses | Admin |

### Role Management

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| `GET` | `/api/roles` | List all roles | Manager/Admin |
| `POST` | `/api/roles` | Create custom role | `manage_roles` |
| `DELETE` | `/api/roles/{role_id}` | Delete custom role | `manage_roles` |

### Audit & Monitoring

| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| `GET` | `/api/audit/logs` | Query audit logs (filterable) | `view_logs` |
| `GET` | `/api/audit/export/json` | Export signed JSON snapshot | `view_logs` |
| `GET` | `/api/audit/export/csv` | Export CSV report | `view_logs` |
| `GET` | `/api/audit/statistics` | Dashboard statistics | `view_logs` |
| `GET` | `/api/health` | Service health check | Public |

---

## 🔒 Security

### Authentication Flow

```
1. POST /api/login { username, password }
2. Server validates credentials (bcrypt)
3. On success → returns { access_token, refresh_token }
4. Client stores tokens and sends: Authorization: Bearer <access_token>
5. Backend decodes JWT → extracts user_id → loads User from DB
6. RBAC middleware checks User.role_rel.permissions for required action
```

### Account Lockout

| Parameter | Value |
|-----------|-------|
| Max failed attempts | 5 |
| Lockout duration | 15 minutes |
| Lockout response code | `423 Locked` |
| Admin override | `PUT /api/users/{id}/unlock` |

### Input Validation

- **Usernames**: 3–50 chars, alphanumeric, must start with a letter
- **Passwords**: 8–128 chars, requires uppercase + lowercase + digit + special character
- **Filenames**: Stripped of traversal patterns, null bytes, hidden file prefixes, blocked extensions
- **Role names**: 2–50 chars, letters/numbers/spaces/hyphens only
- **Permissions**: Validated against allowlist (`upload`, `download`, `rename`, `delete`, `view_logs`, `manage_roles`)

### File Security

- Files encrypted with **Fernet** (AES-128-CBC + HMAC-SHA256) before database storage
- SHA-256 checksums for integrity verification
- Blocked executable extensions: `.exe`, `.bat`, `.cmd`, `.ps1`, `.vbs`, `.sh`, and more
- 100 MB upload size limit (configurable)

---

## 👥 Role-Based Access Control

### Default Role Hierarchy

```
Admin (Protected)
├── All permissions + manage_roles
├── Cannot be deleted or demoted
├── Can assign Manager / Standard User roles
└── Can unlock locked accounts

Manager
├── upload, download, rename, delete, view_logs
├── Can promote Standard Users → Manager
├── Can grant/revoke per-file permissions
└── Can delete Standard Users

Standard User
├── upload, download (own files only)
├── Can view files with explicit permission
├── Cannot manage other users
└── Cannot access audit logs
```

### Permission Matrix

| Action | Admin | Manager | Standard User |
|--------|:-----:|:-------:|:-------------:|
| Upload files | ✅ | ✅ | ✅ |
| Download any file | ✅ | ✅ | ❌ (own + permitted) |
| Rename files | ✅ | ✅ | ✅ (own only) |
| Delete files | ✅ | ✅ | ✅ (own only) |
| View audit logs | ✅ | ✅ | ❌ |
| Manage roles | ✅ | ❌ | ❌ |
| Manage users | ✅ | ✅ (limited) | ❌ |
| Grant file permissions | ✅ | ✅ | ❌ |
| Create custom roles | ✅ | ❌ | ❌ |

---

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `mysql+pymysql://admin:password@db:3306/securevault` | SQLAlchemy connection string |
| `JWT_SECRET` | `your_secret_key` | **Change in production!** JWT signing key |
| `STORAGE_MODE` | `database` | Storage backend: `database`, `filesystem`, `s3` |
| `STORAGE_PATH` | `./file_storage` | Local path for filesystem mode |
| `ENCRYPTION_KEY` | (built-in dev key) | Fernet encryption key (32-byte base64) |
| `LOG_LEVEL` | `info` | Application log level |
| `FRONTEND_URL` | `http://localhost` | CORS allowed origin |

> ⚠️ **Always override `JWT_SECRET` and `ENCRYPTION_KEY` in production deployments.**

---

## 🧑‍💻 Development

### Running Without Docker

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=mysql+pymysql://admin:password@localhost:3306/securevault

# Run the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend

Serve the `frontend/` directory with any static file server:

```bash
cd frontend
python -m http.server 80
# Or use: npx serve .
```

#### Database Seeding

```bash
cd backend
python seed.py
```

### Running with Docker

```bash
# Build and start all services
docker compose up --build

# View logs
docker compose logs -f api

# Stop all services
docker compose down

# Reset database (removes volume)
docker compose down -v
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) — Python SQL toolkit and ORM
- [Docker](https://www.docker.com/) — Container platform
- [Inter](https://rsms.me/inter/) & [JetBrains Mono](https://www.jetbrains.com/lp/mono/) — Typography

---

<p align="center">
  Built with 🔒 by <a href="https://github.com/yuvrajnagarkoti">Yuvraj Nagarkoti</a>
</p>
