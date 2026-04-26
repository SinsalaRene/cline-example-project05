# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x | Yes |
| 2.x | Yes |

## Reporting a Vulnerability

Please report security vulnerabilities to:

- **Security email**: security@example.com
- **Private GitHub issue**: [vulnerabilities](../../security/advisories/new)
- **PGP Key**: Available at `https://example.com/security.pgp`

### Disclosure Policy

1. Send details to security@example.com
2. Respond within 48 hours with next steps
3. No need to wait for response before reporting
4. We will not look back at your data

## Security Practices

### Authentication

- JWT tokens with rotation and revocation support
- Short-lived access tokens (15 minutes)
- Secure refresh tokens (httpOnly, SameSite)
- Rate limiting on authentication endpoints (10 req/min per IP)

### Authorization

- Role-based access control (RBAC)
- Fine-grained permissions per endpoint
- Audit logging of all access decisions

### Data Protection

- All secrets managed via environment variables
- Database connection pooling with SSL/TLS support
- Sensitive data encrypted at rest (AES-256)
- Passwords hashed with bcrypt (cost factor 12)

### API Security

- Security headers on all responses:
  ```
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block
  Strict-Transport-Security: max-age=63072000
  Content-Security-Policy: default-src 'self'
  ```
- Request ID tracking for correlation
- CORS configured per environment
- Input validation with Pydantic schemas

### Infrastructure Security

- TLS 1.3 for all external connections
- Regular dependency scanning in CI/CD pipeline
- Docker image scanning (Trivy/Snyk)
- Network policies in Kubernetes
- Pod security policies (restricted)

### Monitoring

- Structured JSON logging (no PII in logs)
- Health check endpoints for all services
- Alerting on error rate spikes
- Backup verification tests

## Dependencies

### Scanning

```bash
# Backend dependency scanning
cd backend && pip-audit

# Frontend dependency scanning
cd frontend && npm audit

# Docker image scanning
docker scan backend:latest
```

### Supported Dependencies

| Package | Minimum Version | Max Vulnerability |
|---------|----------------|-------------------|
| Python (FastAPI) | 3.11 | Low |
| Angular | 17 | Low |
| PostgreSQL | 14 | Low |
| Redis | 7 | Low |

## Compliance

### Standards

- OWASP Top 10 compliance
- GDPR data handling
- SOC 2 Type II controls

### Audit Schedule

| Audit Type | Frequency | Scope |
|------------|-----------|-------|
| Dependency scan | Every commit | All packages |
| Penetration test | Quarterly | External endpoints |
| Code review | Every PR | All changes |
| Access review | Monthly | User roles |