# Developer Documentation

## Local Development Setup

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### Quick Start

```bash
# Clone the repository
git clone <repo-url>
cd cline-example-project05

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker compose up -d

# Run migrations
docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python scripts/seed_data.py

# Access the application
echo "Frontend: http://localhost"
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/api/docs"
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Azure Cloud Deployment                   │
│                                                       │
│  ┌────────────────┐    ┌──────────────────┐          │
│  │  Frontend App  │    │  Backend App     │          │
│  │  (Angular 17)  │◀──▶│  (FastAPI/Async) │          │
│  └────────────────┘    └──────────────────┘          │
│                              │                        │
│  ┌────────────────┐         ▼                         │
│  │ Redis Cache    │  ┌──────────────┐                 │
│  │ (Celery Broker)│  │ PostgreSQL   │                 │
│  └────────────────┘  │  (v14)       │                 │
│                      └──────────────┘                 │
└─────────────────────────────────────────────────────┘
```

### Component Diagram

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser    │────▶│   Angular    │────▶│   Nginx     │
│   (Client)   │◀───│   App        │     │   Reverse    │
└─────────────┘     │              │     │   Proxy      │
                    │   Services   │     └──────┬───────┘
                    └──────────────┘            │
            ┌───────────────────────────────────┼─────────────────────────────┐
            │              Azure App Proxy        │                           │
            │              (Production)           │                           │
            └───────────────────────────────────────┬───────────────────────┘
                                                    │
              ┌─────────────────────────────────────┼─────────────────────┐
              ▼                                     ▼                     ▼
    ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
    │   Backend       │        │   PostgreSQL    │        │   Redis         │
    │   (FastAPI)     │◀──────▶│   (v14)         │        │   (Celery)      │
    │                 │        │                 │        │                 │
    │  - Auth         │        │  - Rules        │        │  - Tasks        │
    │  - Routers      │        │  - Approvals    │        │  - Cache        │
    │  - Services     │        │  - Audit Log    │        │                 │
    │  - Tasks        │        └─────────────────┘        └─────────────────┘
    │                 │                    │
    │  - Celery      │                    │
    │    Worker       │                    │
    └─────────────────┘                    │
                                           ▼
                                  ┌─────────────────┐
                                  │   Azure Firewall│
                                  │   Manager       │
                                  └─────────────────┘
```

### Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | Python/FastAPI | 3.11+ |
| Frontend | Angular | 17+ |
| Database | PostgreSQL | 14+ |
| Cache | Redis | 7+ |
| Task Queue | Celery | 5+ |
| Container | Docker | 24+ |
| Orchestration | Kubernetes | 1.28+ |
| CI/CD | GitHub Actions | - |

## Code Structure

### Backend (Python/FastAPI)

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment configuration
│   ├── database.py          # Async SQLAlchemy setup
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic schemas
│   ├── logging_config.py    # Structured logging
│   ├── middleware/          # Request/Response middleware
│   ├── tasks/               # Celery background tasks
│   ├── auth/                # Authentication module
│   ├── routers/             # API route definitions
│   └── services/            # Business logic layer
├── tests/                   # Test suite
├── scripts/                 # Helper scripts
└── alembic/                 # Database migrations
```

### Frontend (Angular 17)

```
frontend/src/app/
├── core/                    # Core services & interceptors
│   ├── interceptors/        # HTTP interceptors
│   ├── guards/              # Route guards
│   └── services/            # Core services (Auth)
├── shared/                  # Shared components & services
│   ├── components/          # Reusable UI components
│   ├── services/            # Shared services
│   └── directives/          # Custom directives
├── features/                # Lazy-loaded feature modules
│   ├── auth/                # Authentication
│   ├── dashboard/           # Dashboard & statistics
│   ├── rules/               # Firewall rule management
│   └── approvals/           # Approval workflow
└── app.component.ts         # Root component
```

## Development Workflow

### Backend Development

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

### Frontend Development

```bash
# Install dependencies
cd frontend
npm install

# Start development server
ng serve --port 4200

# Run tests
ng test --watch=false
ng lint

# Build for production
ng build --configuration=production
```

### Full Stack with Docker Compose

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop all services
docker compose down

# Rebuild and restart
docker compose up -d --build
```

## Coding Standards

### Python

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guide
- Use [ruff](https://github.com/astral-sh/ruff) for linting
- Use [mypy](https://mypy.readthedocs.io/) for type checking
- Use [black](https://black.readthedocs.io/) for code formatting
- Maximum line length: 100 characters
- Use type hints for all function signatures

### TypeScript/Angular

- Follow [Airbnb TypeScript style guide](https://github.com/airbnb/javascript/tree/master/typescript)
- Use [ESLint](https://eslint.org/) with [@angular-eslint](https://github.com/angular-eslint/angular-eslint)
- Use [Prettier](https://prettier.io/) for code formatting
- Use strict mode in tsconfig
- Follow Angular style guide: https://angular.io/guide/styleguide

### Commit Messages

Use [conventional commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:

| Type | Description |
|------|-------------|
| feat | A new feature |
| fix | A bug fix |
| docs | Documentation only changes |
| style | Code style changes (formatting, etc.) |
| refactor | A code change that neither fixes a bug nor adds a feature |
| perf | A code change that improves performance |
| test | Adding missing tests or correcting existing tests |
| chore | Changes to the build process or auxiliary tools |

### Branch Strategy

```
main (production)
  │
  └─ develop
       │
       ├─ feature/add-new-endpoint
       ├─ fix/security-header-issue
       └─ refactor/database-connection
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

## Running Tests

### Backend Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_auth.py -v
```

### Frontend Tests

```bash
# Run unit tests
ng test --watch=false

# Run E2E tests
cd e2e && npx cypress run
```

## Adding a New Endpoint

1. Create the model in `app/models.py` (if needed)
2. Create the schema in `app/schemas.py`
3. Create the service in `app/services/`
4. Create the router in `app/routers/`
5. Register the router in `app/main.py`
6. Add tests in `tests/`
7. Update API documentation

## Debugging

### Backend

```python
# Structured logging is available
from app.logging_config import get_logger

logger = get_logger(__name__)
logger.info("Processing rule", rule_id=rule_id)
logger.error("Failed to create rule", exc_info=True)
```

### Frontend

- Use Angular DevTools browser extension
- Check network tab for API calls
- Use `console.log()` with the structured logger pattern

## CI/CD Integration

```bash
# Run the full pipeline locally
docker compose run --rm backend pytest tests/ -v
cd frontend && npm run lint && npm test -- --watch=false