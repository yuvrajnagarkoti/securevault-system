# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ Active  |

## Reporting a Vulnerability

If you discover a security vulnerability in SecureVault, **please do NOT open a public issue**.

### How to Report

1. **Email**: Send details to [yuvraj.nagarkoti@email.com](mailto:yuvraj.nagarkoti@email.com)
2. **Subject line**: `[SECURITY] SecureVault - Brief description`
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

| Action | Timeframe |
|--------|-----------|
| Acknowledgment | 48 hours |
| Initial assessment | 5 business days |
| Fix development | 14 business days |
| Public disclosure | After fix is released |

## Security Features

SecureVault implements the following security measures:

- **Authentication**: JWT-based with access + refresh tokens
- **Password Security**: Bcrypt hashing with salt
- **Account Lockout**: Auto-lock after 5 failed attempts (15-min cooldown)
- **Encryption at Rest**: Fernet (AES-128-CBC + HMAC-SHA256) for stored files
- **Input Validation**: Filename sanitization, blocked executable extensions, SQL injection prevention
- **Rate Limiting**: Per-endpoint throttling via SlowAPI
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, XSS-Protection
- **RBAC**: Role-based and per-file granular permission checks
- **Audit Trail**: Immutable, SHA-256 signed logs for all operations

## Production Deployment Checklist

Before deploying to production, ensure:

- [ ] `JWT_SECRET` is set to a strong, unique value
- [ ] `ENCRYPTION_KEY` is set to a unique Fernet key
- [ ] Default admin password is changed
- [ ] MySQL root password is changed from default
- [ ] CORS origins are restricted to your domain
- [ ] HTTPS is configured (via reverse proxy)
- [ ] Docker containers run as non-root users
- [ ] Database backups are configured
- [ ] Log monitoring and alerting is set up

## Known Limitations

- Refresh token rotation is not yet implemented
- CSRF tokens are not used (JWT Bearer auth mitigates this)
- File encryption key rotation requires manual re-encryption of existing files
