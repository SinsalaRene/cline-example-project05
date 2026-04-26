# Changelog

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