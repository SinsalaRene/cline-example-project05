# Azure Firewall Manager

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