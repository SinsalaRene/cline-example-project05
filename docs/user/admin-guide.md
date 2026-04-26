# Admin User Guide

## Overview

The Azure Firewall Manager allows security teams to manage Azure firewall rules through a web-based approval workflow.

## Getting Started

1. Access the application at the provided URL
2. Login with your Azure AD credentials
3. Navigate to Dashboard for overview

### Dashboard

The dashboard provides a real-time overview of:

- Total firewall rules across all landing zones
- Rules pending approval
- Rules by status (draft, approved, deployed, rejected)
- Rules by landing zone (dev, staging, prod)
- Recent activity log

## Managing Rules

### Creating a Rule

1. Click "Create Rule"
2. Fill in required fields:
   - **Rule name**: Unique identifier for the rule
   - **Landing zone**: Target Azure environment (dev, staging, prod)
   - **Rule collection name**: Group name for related rules
   - **Action**: Allow or Deny traffic
   - **Priority**: 100-10000 (lower number = higher priority)
3. Add optional fields:
   - **Destination addresses**: IP ranges or `*` for all
   - **Destination ports**: List of ports (e.g., `80`, `443`, `8080-9000`)
   - **Destination FQDNs**: Domain names (e.g., `*.example.com`)
   - **Protocol**: tcp, udp, or *
   - **Notes**: Additional context for approvers
4. Submit for approval

### Rule Statuses

| Status | Description | Can Edit | Can Delete |
|--------|-------------|----------|------------|
| Draft | Created but not submitted | Yes | Yes |
| Pending Approval | Awaiting review | No | No |
| Approved | Approved, awaiting deployment | No | No |
| Deployed | Successfully deployed to Azure | No | No |
| Rejected | Rejected by approver | Yes | Yes |
| Deleted | Soft-deleted (recoverable) | No | No |

### Approval Workflow

Rules follow a staged approval process:

1. **Draft** -> **Pending Approval**: When submitted
2. **Pending Approval** -> **Approved**: When approver accepts
3. **Pending Approval** -> **Rejected**: When approver declines
4. **Approved** -> **Deployed**: When deployment completes
5. **Rejected** -> **Draft**: When resubmitted

#### Approval Requirements

| Landing Zone | Requires Approval | Approvers |
|--------------|-------------------|-----------|
| dev | Optional | Team lead |
| staging | Required | Security team |
| prod | Required | Security team + Manager |

### Viewing Rules

1. Navigate to **Rules > Firewall Rules**
2. Use the filter bar to find specific rules:
   - **Status**: Filter by rule status
   - **Landing zone**: Filter by target environment
   - **Action**: Filter by Allow/Deny
   - **Search**: Text search across rule names and notes
3. Click a rule to view:
   - Full rule details
   - Approval history
   - Deployment history
   - Audit log entries

### Editing Rules

1. Find and select the rule from the list
2. Click **Edit** (only available for Draft and Rejected rules)
3. Modify the desired fields
4. Click **Save** (saves as Draft) or **Resubmit** (sends for approval)

### Deleting Rules

1. Find and select the rule
2. Click **Delete**
3. Confirm deletion in the dialog
4. Rule is soft-deleted and can be restored within 30 days

## Approvals

### Viewing Pending Approvals

1. Navigate to **Approvals**
2. Review pending requests:
   - Rule name and details
   - Requestor information
   - Priority and landing zone
   - Request date

### Approving a Rule

1. Click **Review** on the pending approval
2. Examine the rule configuration:
   - Rule details
   - Potential impact
   - Requestor notes
3. Click **Approve** or **Reject**
4. Add notes (required for rejections)

### Approval Actions

| Action | Result | Notification |
|--------|--------|--------------|
| Approve | Rule moves to Approved status | Requestor |
| Reject | Rule moves to Rejected status | Requestor |
| Request Info | Adds comment, status remains pending | Requestor |

## User Management

### Viewing Users

Navigate to **Admin > Users** to view:

- Active users
- User roles
- Last login time
- Created rules count

### Assigning Roles

| Role | Permissions |
|------|-------------|
| Viewer | View rules and dashboard only |
| Creator | Create and edit rules |
| Approver | Approve/reject rules |
| Admin | Full access + user management |

## Export

### Exporting Rules

1. Navigate to **Rules > Firewall Rules**
2. Click **Export CSV**
3. Choose filter options:
   - All rules or filtered view
   - Include deleted rules
4. Download the CSV file

### CSV Format

The exported CSV includes:

```
ID,Name,Collection,Action,Priority,Status,Landing Zone,Dest Addresses,Dest Ports,Dest FQDNs,Created By,Created At,Updated At
```

## Audit Log

### Viewing Audit Entries

Navigate to **Admin > Audit Log** to see:

| Field | Description |
|-------|-------------|
| Timestamp | When the event occurred |
| User | Who performed the action |
| Action | Type of action (CREATE, UPDATE, DELETE, APPROVE, REJECT) |
| Entity | Resource affected |
| Details | Additional context |

### Audit Retention

- Active audit log: 90 days
- Archived: 1 year
- Exportable for compliance

## Notifications

### Notification Channels

- **Email**: Primary notification method
- **In-app**: Bell icon in top navigation
- **Webhook**: Configurable for approvals (Admin setting)

### Email Notifications

| Event | Recipients |
|-------|------------|
| Rule Created | Approvers |
| Rule Approved | Requestor |
| Rule Rejected | Requestor |
| Rule Deployed | Requestor |
| Rule Expired | Requestor + Admin |

## Settings

### Configurable Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Default Priority | 500 | New rule default priority |
| Require Notes on Reject | Yes | Force approver to add notes |
| Auto-Deploy Approved | No | Auto-deploy after approval |
| Password Policy | Standard | Enforce strong passwords |
| Session Timeout | 30 min | Auto-logout after inactivity |
</content>
<write_to_file>
<path>SECURITY.md</path>
<content># Security Policy

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
</content>
<write_to_file>
<path>CHANGELOG.md</path>
<content># Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-06-15

### Added

- Async database engine for improved concurrency (Session 1)
- Security headers middleware (CORS, CSP, HSTS) (Session 1)
- Request ID tracking for distributed tracing (Session 1)
- Structured JSON logging with correlation IDs (Session 1)
- API versioning (`/api/v1/`) (Session 1)
- Dashboard statistics endpoint with aggregation (Session 1)
- CSV export functionality for firewall rules (Session 2)
- Celery background task infrastructure (Session 3)
- Alembic database migrations with upgrade/downgrade (Session 3)
- Soft delete support for firewall rules (Session 3)
- Versioning support for audit trail (Session 3)
- External ID support for Azure integration (Session 3)
- Angular Material UI component library (Session 4)
- HTTP interceptors for auth tokens and error handling (Session 4)
- Auth guards for route protection (Session 4)
- Dashboard with charts and statistics display (Session 4)
- Comprehensive test suite with pytest (Session 5)
- Jest unit tests for Angular components (Session 5)
- E2E tests with Cypress (Session 5)
- GitHub Actions CI/CD pipelines (Session 6)
- Terraform infrastructure modules for Azure (Session 6)
- Bicep templates for Azure resource provisioning (Session 6)
- Kubernetes deployment manifests (Session 6)
- Docker multi-stage builds for optimized images (Session 6)

### Changed

- Migrated from synchronous SQLAlchemy to async (asyncpg)
- Updated to Angular 17 with standalone components
- Updated Docker images to use multi-stage builds
- Enhanced JWT with token refresh support
- Improved error handling with custom middleware

### Fixed

- Hardcoded secrets replaced with environment variables
- Missing security headers added to all responses
- CORS configuration updated for production domains

### Deprecated

- None (v2.0.0 is a clean upgrade)

### Removed

- Synchronous database driver (replaced with asyncpg)
- Inline styles (migrated to Angular Material)

---

## [1.0.0] - 2024-01-01

### Added

- Initial project structure
- Basic FastAPI backend with CRUD for firewall rules
- Basic Angular frontend with Material components
- SQLite database for local development
- Simple authentication with JWT
- Docker Compose setup for local development
</content>
<write_to_file>
<path>README.md</path>
<content># Azure Firewall Manager

A comprehensive platform for managing Azure firewall rules with a web-based approval workflow.

## Quick Start

```bash
# Start the application
docker compose up -d

# Access at http://localhost
# API docs at http://localhost:8000/api/docs
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | `postgresql+asyncpg://postgres:password@localhost:5432/fw_portal` |
| SECRET_KEY | JWT signing key | **Must be set** |
| AZURE_TENANT_ID | Azure AD tenant ID | Required in production |
| AZURE_CLIENT_ID | Azure AD client ID | Required in production |
| AZURE_CLIENT_SECRET | Azure AD client secret | Required in production |
| REDIS_URL | Redis connection URL | `redis://localhost:6379/0` |
| CELERY_BROKER_URL | Celery message broker | Same as REDIS_URL |
| LOG_LEVEL | Logging verbosity | `INFO` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DEBUG | Enable debug mode | `false` |
| CORS_ORIGINS | Comma-separated allowed origins | `http://localhost,http://127.0.0.1` |
| JWT_EXPIRES_MIN | Access token expiry in minutes | `15` |
| JWT_REFRESH_EXPIRES_DAYS | Refresh token expiry in days | `7` |
| PASSWORD_BCRYPT_COST | Bcrypt cost factor | `12` |

## Project Structure

```
cline-example-project05/
├── backend/          # FastAPI backend (Python 3.11+)
│   ├── app/          # Application code
│   ├── tests/        # Test suite
│   ├── scripts/      # Helper scripts
│   └── alembic/      # Database migrations
├── frontend/         # Angular 17 frontend
│   ├── src/app/      # Application code
│   └── e2e/          # E2E tests (Cypress)
├── infrastructure/   # Infrastructure as Code
│   ├── terraform/    # Terraform modules
│   └── bicep/        # Bicep templates
├── kubernetes/       # Kubernetes deployment manifests
├── docs/             # Documentation
│   ├── api/          # API reference
│   ├── developer/    # Developer guide
│   ├── operations/   # Operations runbooks
│   └── user/         # User documentation
├── .github/          # GitHub Actions CI/CD workflows
└── .env.example      # Environment template
```

## API Documentation

OpenAPI docs: http://localhost:8000/api/docs
Postman collection: [POSTMAN_COLLECTION.json](POSTMAN_COLLECTION.json) (import into Postman)

### Quick API Test

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# Get dashboard stats
curl http://localhost:8000/api/v1/stats/dashboard \
  -H "Authorization: Bearer <your-token>"
```

## Testing

```bash
# Backend tests
cd backend && pytest tests/ -v --cov=app

# Backend tests with coverage report
cd backend && pytest tests/ --cov=app --cov-report=html

# Frontend unit tests
cd frontend && ng test --watch=false

# Frontend E2E tests
cd frontend/e2e && npx cypress run
```

## Deployment

### Local Development

```bash
docker compose up -d
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python scripts/seed_data.py
```

### Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -f kubernetes/

# Set environment variables
kubectl create secret generic backend-secret \
  --from-literal=secret-key=<key> \
  --from-literal=database-url=<url> \
  --from-literal=redis-url=<url>

# Scale deployments
kubectl scale deployment/backend --replicas=2
kubectl scale deployment/frontend --replicas=2
```

### Azure (Infrastructure as Code)

```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Preview changes
terraform plan -var-file=environments/production.tfvars

# Apply changes
terraform apply -var-file=environments/production.tfvars
```

See [docs/operations/deployment-runbook.md](docs/operations/deployment-runbook.md) for detailed procedures.

## Security

See [SECURITY.md](SECURITY.md) for security policy, vulnerability reporting, and practices.

### Security Best Practices

- Always use HTTPS in production
- Rotate JWT secret keys regularly
- Enable Azure Monitor and Log Analytics
- Run dependency scans in CI/CD
- Restrict access to PostgreSQL (private subnet only)

## Documentation

- [API Documentation](docs/api/README.md)
- [Developer Guide](docs/developer/README.md)
- [Architecture Decision Records](docs/developer/architecture-decision-records.md)
- [Operations Runbook](docs/operations/deployment-runbook.md)
- [Backup & Restore Procedures](docs/operations/backup-restore.md)
- [Admin User Guide](docs/user/admin-guide.md)

## Contributing

1. Follow the branch strategy: `feature -> develop -> main`
2. Use conventional commit messages
3. Ensure all CI checks pass
4. Get code review approval from maintainers

## License

This project is licensed under the MIT License.