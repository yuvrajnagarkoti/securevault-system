# Contributing to SecureVault

Thank you for considering contributing to SecureVault! This document provides guidelines for contributing.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/securevault-system.git
   cd securevault-system
   ```
3. **Add upstream** remote:
   ```bash
   git remote add upstream https://github.com/yuvrajnagarkoti/securevault-system.git
   ```
4. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose

### Running Locally

```bash
docker compose up --build
```

Or run the backend directly (requires local MySQL):

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Branch Naming

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New features | `feature/s3-storage-adapter` |
| `fix/` | Bug fixes | `fix/lockout-timer-display` |
| `docs/` | Documentation | `docs/api-examples` |
| `refactor/` | Code refactoring | `refactor/storage-layer` |
| `security/` | Security fixes | `security/jwt-rotation` |

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(auth): add OAuth2 provider support
fix(storage): resolve encryption key rotation bug
docs(readme): update API reference table
```

## Pull Request Process

1. Update your branch with the latest upstream changes
2. Ensure all services start without errors via `docker compose up --build`
3. Test your changes manually through the UI and API
4. Update documentation if you've changed APIs or behavior
5. Submit a PR with a clear description

### PR Checklist

- [ ] Code follows project coding standards
- [ ] All endpoints have proper RBAC checks
- [ ] Input validation is applied to new endpoints
- [ ] Audit logging is added for administrative actions
- [ ] No secrets or credentials are hardcoded
- [ ] Docker services build and run correctly

## Coding Standards

### Python (Backend)

- Follow **PEP 8** style guide
- Use **type hints** for function signatures
- Include **docstrings** for all functions and classes
- Use **SQLAlchemy ORM** for database operations (no raw SQL)
- Validate all user input before processing
- Log administrative actions via `audit.log_action()`

### JavaScript (Frontend)

- Use vanilla JS (no frameworks)
- Follow camelCase naming convention
- Handle API errors with user-friendly toast notifications

### CSS

- Use CSS custom properties for theming
- Keep responsive breakpoints consistent

## Reporting Bugs

Please include:

1. **Description** of the issue
2. **Steps to reproduce**
3. **Expected** vs **actual** behavior
4. **Environment** (OS, browser, Docker version)
5. **Screenshots or logs** if applicable

## Feature Requests

Describe the problem, proposed solution, alternatives considered, and any additional context.

---

Thank you for helping make SecureVault better! 🛡️
