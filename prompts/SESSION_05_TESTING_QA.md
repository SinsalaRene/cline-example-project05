# Session 5: Testing & Quality Assurance

## Context

You are working on the Azure Firewall Manager application. Sessions 1-4 (Security, API, Database, Frontend) have been completed. Now we build a comprehensive test suite for both backend and frontend.

## Project Structure (After Sessions 1-4)

```
cline-example-project05/
├── backend/
│   ├── app/
│   │   ├── main.py              # Async FastAPI app
│   │   ├── config.py            # Environment config
│   │   ├── database.py          # Async SQLAlchemy
│   │   ├── models.py            # Enhanced models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── logging_config.py
│   │   ├── middleware/
│   │   ├── tasks/
│   │   ├── auth/
│   │   ├── routers/
│   │   └── services/
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_rules.py
│   │   ├── test_approvals.py
│   │   ├── test_stats.py
│   │   ├── test_export.py
│   │   └── fixtures/
│   │       ├── __init__.py
│   │       └── data.py
│   ├── pytest.ini
│   └── pyproject.toml
├── frontend/
│   ├── e2e/
│   │   ├── cypress/
│   │   │   ├── fixtures/
│   │   │   ├── e2e/
│   │   │   ├── support/
│   │   │   └── cypress.config.ts
│   │   └── package.json
│   └── src/
│       └── app/
│           ├── *.component.spec.ts
│           └── shared/
│               ├── *.service.spec.ts
│               └── core/
│                   └── *.interceptor.spec.ts
├── docker-compose.yml
└── .env.example
```

## Tasks

### Task 5.1: Backend Test Configuration (`backend/pytest.ini`)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
    --maxfail=1
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

Create `backend/tests/conftest.py`:

```python
"""Pytest fixtures for backend testing."""
import asyncio
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import get_pool_extension
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import Session

from app.config import settings, Environment
from app.database import Base, get_db, engine
from app.main import app
from app.models import User, FirewallRule, Tag, ApprovalRecord
from app.schemas import RuleAction, RuleStatus, ResourceCategory, ApprovalStatus


# Override settings for testing
@pytest.fixture(autouse=True)
def override_settings():
    """Override settings with test-specific values."""
    original_debug = settings.DEBUG
    settings.DEBUG = True
    settings.DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_fw_portal"
    settings.SECRET_KEY = "test-secret-key-for-testing-only-do-not-use-in-production"
    settings.ENVIRONMENT = Environment.DEVELOPMENT
    settings.ALLOWED_HOSTS = ["*"]
    yield
    settings.DEBUG = original_debug


@pytest.fixture
async def db_client():
    """Database client for testing with transaction rollback."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest.fixture
async def superuser(db_client):
    """Create a superuser for testing."""
    user = User(
        oidc_sub="test-sub-super",
        email="super@example.com",
        display_name="Super User",
        role="admin",
        is_active=True,
    )
    db_client.add(user)
    await db_client.commit()
    return user


@pytest.fixture
async def sample_rule(superuser, db_client):
    """Create a sample firewall rule for testing."""
    rule = FirewallRule(
        name="Test Rule",
        description="A test firewall rule",
        landing_zone="corp",
        rule_collection_name="Test Collection",
        priority=100,
        action=RuleAction.ALLOW,
        status=RuleStatus.DRAFT,
        created_by_id=superuser.id,
    )
    db_client.add(rule)
    await db_client.commit()
    await db_client.refresh(rule)
    return rule


@pytest.fixture
async def sample_tags(db_client):
    """Create sample tags."""
    tags = [
        Tag(name="production", color="#ff0000"),
        Tag(name="staging", color="#ffaa00"),
    ]
    db_client.add_all(tags)
    await db_client.commit()
    return tags
```

### Task 5.2: Test Fixtures (`backend/tests/fixtures/data.py`)

```python
"""Test data fixtures for backend tests."""
from app.config import RuleAction, RuleStatus, ResourceCategory, ApprovalStatus


def sample_rule_data():
    """Return sample firewall rule data."""
    return {
        "name": "Allow HTTPS Inbound",
        "description": "Allow HTTPS from internet",
        "landing_zone": "corp",
        "rule_collection_name": "Corporate Rules",
        "priority": 100,
        "action": "allow",
        "destination_ports": ["443"],
        "category": "network",
        "environment": "production",
    }


def sample_users():
    """Return sample users."""
    return [
        {"oidc_sub": "user-1", "email": "admin@example.com", "role": "admin"},
        {"oidc_sub": "user-2", "email": "security@example.com", "role": "security_stakeholder"},
        {"oidc_sub": "user-3", "email": "workload@example.com", "role": "workload_stakeholder"},
    ]


def sample_approval_data():
    """Return sample approval data."""
    return {
        "action": "approve",
        "notes": "Approved for production",
    }
```

### Task 5.3: Auth Tests (`backend/tests/test_auth.py`)

```python
"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import RuleAction, RuleStatus


@pytest.mark.integration
class TestAuthEndpoints:
    """Tests for auth endpoints."""

    @pytest.mark.asyncio
    async def test_login_success(self, db_client, sample_rule_data):
        """Test successful login with valid credentials."""
        # Create a test user
        user = User(
            oidc_sub="test-login-user",
            email="login@example.com",
            display_name="Login User",
            role="admin",
        )
        db_client.add(user)
        await db_client.commit()

        response = await db_client.execute(
            select(User).where(User.email == "login@example.com")
        )
        assert user is not None

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "invalid@example.com", "password": "wrong"}
            )
            assert response.status_code == 401


class TestAuthMiddleware:
    """Tests for auth middleware."""

    def test_require_role_admin(self, superuser):
        """Test that admin role passes require_role check."""
        assert superuser.role == "admin"

    def test_require_role_restricted(self, sample_rule):
        """Test that non-admin role fails require_role check."""
        assert sample_rule.action == RuleAction.ALLOW


class TestTokenGeneration:
    """Tests for token generation."""

    def test_access_token_generated(self):
        """Test that access tokens can be generated."""
        from app.auth.auth import create_access_token, settings
        import jwt
        token = create_access_token({"sub": "test-user", "role": "admin"})
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded["sub"] == "test-user"
        assert decoded["type"] == "access"

    def test_refresh_token_has_different_expiry(self):
        """Test that refresh tokens have longer expiry."""
        from app.auth.auth import create_access_token, create_refresh_token
        access = create_access_token({"sub": "test"})
        refresh = create_refresh_token({"sub": "test"})
        assert access != refresh
```

### Task 5.4: Rules Tests (`backend/tests/test_rules.py`)

```python
"""Tests for firewall rule endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport

from app.models import FirewallRule


class TestRuleEndpoints:
    """Tests for rule CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_rule(self, db_client, sample_rule_data):
        """Test creating a new firewall rule."""
        rule = FirewallRule(
            name=sample_rule_data["name"],
            description=sample_rule_data["description"],
            landing_zone=sample_rule_data["landing_zone"],
            rule_collection_name=sample_rule_data["rule_collection_name"],
            priority=sample_rule_data["priority"],
            action=RuleAction.ALLOW,
            status=RuleStatus.DRAFT,
        )
        db_client.add(rule)
        await db_client.commit()
        await db_client.refresh(rule)

        assert rule.id is not None
        assert rule.name == "Allow HTTPS Inbound"
        assert rule.action == RuleAction.ALLOW

    @pytest.mark.asyncio
    async def test_get_rules(self, sample_rule, db_client):
        """Test retrieving list of rules."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/firewalls/rules")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_get_rule_by_id(self, sample_rule, db_client):
        """Test retrieving a single rule by ID."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/firewalls/rules/{sample_rule.id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == sample_rule.id

    @pytest.mark.asyncio
    async def test_update_rule(self, sample_rule, db_client):
        """Test updating a rule."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/firewalls/rules/{sample_rule.id}",
                json={"description": "Updated description"},
            )
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_rule(self, sample_rule, db_client):
        """Test deleting a rule."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete(f"/api/v1/firewalls/rules/{sample_rule.id}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rule_validation(self, sample_rule_data):
        """Test that rule validation works."""
        from app.schemas import FirewallRuleCreate
        invalid_data = {"name": "", "landing_zone": "corp"}
        with pytest.raises(Exception):
            FirewallRuleCreate(**invalid_data)


class TestRuleFiltering:
    """Tests for rule filtering and search."""

    @pytest.mark.asyncio
    async def test_filter_by_landing_zone(self, sample_rule, db_client):
        """Test filtering rules by landing zone."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/firewalls/rules?landing_zone=corp"
            )
            assert response.status_code == 200
            data = response.json()
            for item in data["items"]:
                assert item["landing_zone"] == "corp"

    @pytest.mark.asyncio
    async def test_filter_by_status(self, sample_rule, db_client):
        """Test filtering rules by status."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/firewalls/rules?status=DRAFT"
            )
            assert response.status_code == 200
```

### Task 5.5: Frontend Unit Tests (`frontend/src/app/`)

Create `frontend/src/app/shared/api.service.spec.ts`:

```typescript
import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { environment } from '../../environments/environment';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        ApiService,
        provideHttpClientTesting()
      ]
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should make GET request', fakeAsync(() => {
    service.get('/rules').subscribe(rules => {
      expect(rules).toEqual([{ id: 1, name: 'Test' }]);
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/rules`);
    expect(req.request.method).toBe('GET');
    req.flush([{ id: 1, name: 'Test' }]);
    tick();
  }));

  it('should make POST request with auth header', fakeAsync(() => {
    localStorage.setItem('access_token', 'test-token');
    service.post('/rules', { name: 'Test' }).subscribe();

    const req = httpMock.expectOne(`${environment.apiUrl}/rules`);
    expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
    req.flush({ id: 1 });
    tick();
  }));

  it('should handle 401 errors', fakeAsync(() => {
    service.get('/rules').subscribe(
      () => fail('should have failed'),
      error => expect(error.status).toBe(401)
    );

    httpMock.expectOne(`${environment.apiUrl}/rules`).error(
      new ErrorEvent('error', { message: 'Unauthorized' })
    );
    tick();
  }));
});
```

Create `frontend/src/app/features/rules/rules.component.spec.ts`:

```typescript
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { RulesComponent } from './rules.component';
import { FirewallService } from '../../shared/firewall.service';
import { AuthService } from '../../core/services/auth.service';
import { FirewallRule } from '../../shared/interfaces';

describe('RulesComponent', () => {
  let component: RulesComponent;
  let fixture: ComponentFixture<RulesComponent>;
  let firewallServiceSpy: jasmine.SpyObj<FirewallService>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  beforeEach(async () => {
    const spyFirewall = jasmine.createSpyObj('FirewallService', ['getRules', 'deleteRule']);
    const spyAuth = jasmine.createSpyObj('AuthService', ['getUser', 'hasRole']);

    await TestBed.configureTestingModule({
      imports: [
        RulesComponent,
        MatButtonModule,
        MatTableModule,
        RouterTestingModule
      ],
      providers: [
        { provide: FirewallService, useValue: spyFirewall },
        { provide: AuthService, useValue: spyAuth }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RulesComponent);
    component = fixture.componentInstance;
    firewallServiceSpy = TestBed.inject(FirewallService) as jasmine.SpyObj<FirewallService>;
    authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load rules on init', fakeAsync(() => {
    const mockRules: FirewallRule[] = [
      { id: 1, name: 'Rule 1', status: 'DRAFT' },
      { id: 2, name: 'Rule 2', status: 'ACTIVE' }
    ];
    firewallServiceSpy.getRules.and.returnValue(of({ items: mockRules, total: 2, page: 1, per_page: 50 }));

    fixture.detectChanges();
    tick();

    expect(component.rules).toEqual(mockRules);
    expect(firewallServiceSpy.getRules).toHaveBeenCalled();
  }));

  it('should display rule count', fakeAsync(() => {
    const mockRules: FirewallRule[] = [{ id: 1, name: 'Rule 1', status: 'DRAFT' }];
    firewallServiceSpy.getRules.and.returnValue(of({ items: mockRules, total: 1, page: 1, per_page: 50 }));

    fixture.detectChanges();
    tick();

    const compiled = fixture.nativeElement;
    expect(compiled.querySelector('.stat-value')?.textContent).toContain('1');
  }));
});
```

### Task 5.6: E2E Tests (`frontend/e2e/cypress/`)

Create `frontend/e2e/cypress.config.ts`:

```typescript
import { defineConfig } from "cypress";

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:4200',
    supportFile: 'cypress/support/e2e.ts',
    viewport: { width: 1280, height: 720 },
    video: false,
    screenshotOnRunFailure: true,
  },
  component: {
    spec: 'cypress/e2e/**/*.cy.ts',
  },
});
```

Create `frontend/e2e/cypress/e2e/login.spec.ts`:

```typescript
describe('Login Flow', () => {
  beforeEach(() => {
    cy.visit('/login');
  });

  it('should display login page', () => {
    cy.get('h1').should('contain', 'Login');
    cy.get('input[placeholder="Email"]').should('be.visible');
    cy.get('input[placeholder="Password"]').should('be.visible');
    cy.get('button[type="submit"]').should('contain', 'Login');
  });

  it('should show error for invalid credentials', () => {
    cy.get('input[placeholder="Email"]').type('invalid@example.com');
    cy.get('input[placeholder="Password"]').type('wrongpassword');
    cy.get('button[type="submit"]').click();
    
    cy.get('.error-message').should('be.visible');
  });
});
```

Create `frontend/e2e/cypress/e2e/rules.spec.ts`:

```typescript
describe('Firewall Rules', () => {
  beforeEach(() => {
    cy.login('admin@example.com', 'password');
    cy.visit('/rules');
  });

  it('should display rules table', () => {
    cy.get('table').should('be.visible');
    cy.get('mat-header-cell').should('contain', 'Rule Name');
    cy.get('mat-header-cell').should('contain', 'Status');
    cy.get('mat-header-cell').should('contain', 'Actions');
  });

  it('should filter rules by search', () => {
    cy.get('input[placeholder="Search rules..."]').type('Allow');
    cy.get('mat-row').should('have.length.at.least(1)');
  });

  it('should navigate to rule detail', () => {
    cy.get('mat-row').first().click();
    cy.url().should('include', '/rules/');
  });
});
```

### Task 5.7: Update `docker-compose.yml`

Add test services:

```yaml
  test_backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: fw-portal-test
    command: pytest tests/ -v --junitxml=/tmp/test-results.xml
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/test_fw_portal
    depends_on:
      db:
        condition: service_healthy
    networks:
      - fw-portal-net
    volumes:
      - test_results:/tmp/test-results.xml
    restart: "no"
```

## Testing Commands

```bash
# Backend tests
cd backend
pytest tests/ -v
pytest tests/ --cov=app --cov-report=term-missing

# Frontend tests
cd frontend
ng test --watch=false --browsers=ChromeHeadless

# E2E tests
cd frontend/e2e
npx cypress run

# Full test suite via Docker
docker compose up test_backend
```

## Acceptance Criteria

- [ ] Backend tests cover all service functions
- [ ] Backend integration tests cover all API endpoints
- [ ] Frontend unit tests cover services and components
- [ ] E2E tests cover login and rules workflows
- [ ] Test coverage >= 70% for backend, >= 60% for frontend
- [ ] Docker compose test service runs successfully
- [ ] Test fixtures work correctly