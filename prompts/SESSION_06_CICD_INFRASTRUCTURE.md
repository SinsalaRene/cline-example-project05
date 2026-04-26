# Session 6: CI/CD & Infrastructure as Code

## Context

You are working on the Azure Firewall Manager application. Sessions 1-5 (Security, API, Database, Frontend, Testing) have been completed. Now we set up continuous integration, deployment, and cloud infrastructure.

## Project Structure (After Sessions 1-5)

```
cline-example-project05/
├── backend/                  # Sessions 1-5 completed
├── frontend/                 # Sessions 1-5 completed
├── kubernetes/               # NEW: Kubernetes deployment
│   ├── values.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── infrastructure/
│   ├── terraform/            # NEW: Terraform modules
│   └── bicep/                # NEW: Bicep templates
├── .github/
│   └── workflows/            # NEW: GitHub Actions
│       ├── ci-backend.yml
│       ├── ci-frontend.yml
│       ├── cd-staging.yml
│       └── cd-production.yml
├── docker-compose.yml
└── .env.example
```

## Tasks

### Task 6.1: GitHub Actions CI Backend (`.github/workflows/ci-backend.yml`)

```yaml
name: CI - Backend

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install ruff pylint
          
      - name: Lint with ruff
        run: |
          cd backend
          ruff check app/
          ruff format --check
          
      - name: Type check
        run: |
          cd backend
          mypy app/ --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd="pg_isready"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
          
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
          
      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost:5432/test_fw_portal
          SECRET_KEY: test-secret-key
          REDIS_URL: redis://localhost:6379/0
        run: |
          cd backend
          pytest tests/ -v --cov=app --cov-report=xml --cov-report=term-missing
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: |
          docker build -t firewall-manager-backend:${{ github.sha }} -f backend/Dockerfile backend/
          
      - name: Scan image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: firewall-manager-backend:${{ github.sha }}
          format: table
          exit-code: '0'
          severity: 'CRITICAL,HIGH'
```

### Task 6.2: GitHub Actions CI Frontend (`.github/workflows/ci-frontend.yml`)

```yaml
name: CI - Frontend

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          
      - name: Lint
        run: |
          cd frontend
          npm run lint

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
          
      - name: Run unit tests
        run: |
          cd frontend
          npx ng test --watch=false --browsers=ChromeHeadless --code-coverage=true
          
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: frontend/coverage/lcov.info

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Build
        run: |
          cd frontend
          npm ci
          npm run build -- --configuration production
```

### Task 6.3: GitHub Actions CD Staging (`.github/workflows/cd-staging.yml`)

```yaml
name: CD - Staging

on:
  push:
    branches: [develop]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
          subscription-id: ${{ secrets.STAGING_SUBSCRIPTION }}
          
      - name: Build & Push Backend
        run: |
          az acr login --name ${{ secrets.ACR_NAME }}
          docker build -t ${{ secrets.ACR_NAME }}.azurecr.io/backend:${{ github.sha }} -f backend/Dockerfile .
          docker push ${{ secrets.ACR_NAME }}.azurecr.io/backend:${{ github.sha }}
          
      - name: Build & Push Frontend
        run: |
          docker build -t ${{ secrets.ACR_NAME }}.azurecr.io/frontend:${{ github.sha }} -f frontend/Dockerfile .
          docker push ${{ secrets.ACR_NAME }}.azurecr.io/frontend:${{ github.sha }}
          
      - name: Deploy to AKS
        uses: azure/k8s-deploy@v4
        with:
          namespace: staging
          images: ${{ secrets.ACR_NAME }}.azurecr.io/backend:${{ github.sha }}
          secrets: |
            DB_PASSWORD=${{ secrets.STAGING_DB_PASSWORD }}
            JWT_SECRET=${{ secrets.STAGING_JWT_SECRET }}
```

### Task 6.4: GitHub Actions CD Production (`.github/workflows/cd-production.yml`)

```yaml
name: CD - Production

on:
  push:
    branches: [main]

jobs:
  approval:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Wait for approval
        run: echo "Manual approval required"
        
  deploy:
    runs-on: ubuntu-latest
    needs: approval
    environment: production
    steps:
      - uses: actions/checkout@v4
      
      - name: Login to Azure
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
          subscription-id: ${{ secrets.PROD_SUBSCRIPTION }}
          
      - name: Rollback protection
        run: |
          echo "Running pre-deploy checks..."
          
      - name: Deploy Backend
        run: |
          # Deploy with canary strategy
          az aks upgrade ...
          
      - name: Health Check
        run: |
          # Verify health endpoint
          curl -f https://api.example.com/health || exit 1
          
      - name: Run Smoke Tests
        run: |
          # Run post-deploy smoke tests
          pytest tests/smoke/
```

### Task 6.5: Terraform Modules (`infrastructure/terraform/`)

Create `infrastructure/terraform/main.tf`:

```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "staging"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "westeurope"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "admin_password" {
  description = "Database admin password"
  type        = string
  sensitive   = true
}

provider "azurerm" {
  features {}
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${var.resource_group_name}-${var.environment}"
  location = var.location
  tags = {
    Environment = var.environment
    Project     = "firewall-manager"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "main" {
  name                = "${var.environment}-vnet"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  address_spaces      = ["10.0.0.0/16"]
}

# Subnets
resource "azurerm_subnet" "application" {
  name                 = "application-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.1.0/24"]
}

resource "azurerm_subnet" "database" {
  name                 = "database-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.2.0/24"]
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                        = "${var.environment}-kv"
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_enabled         = true
  purge_protection_enabled    = true
  sku_name                    = "standard"
  
  access_policy {
    object_id   = data.azurerm_client_config.current.object_id
    tenant_id   = data.azurerm_client_config.current.tenant_id
    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover"
    ]
  }
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.environment}-db"
  resource_group_name    = azurerm_resource_group.main.name
  location               = azurerm_resource_group.main.location
  version                = "14"
  administrator_login    = "postgres"
  administrator_password = var.admin_password
  
  delegated_subnet_id  = azurerm_subnet.database.id
  private_ip_address   = "10.0.2.4"
  
  sku_name   = "GP_Gen5_2"
  storage_mb = 32768
  auto_resize = true
  
  backup {
    retention_days = 35
  }
  
  high_availability {
    enabled                      = true
    mode                         = "SameRegion"
    standby_availability_zone    = "1"
  }
  
  tags = {
    Environment = var.environment
  }
}

# Redis Cache
resource "azurerm_redis_cache" "main" {
  name                = "${var.environment}-redis"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = 1
  family              = "C"
  sku_name            = "Basic"
  redis_version       = 6
  
  tags = {
    Environment = var.environment
  }
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "${var.environment}-plan"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "B1"
}

# Backend App Service
resource "azurerm_linux_app_service" "backend" {
  name                = "${var.environment}-backend"
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id
  
  container_registry_login = azurerm_container_registry.main.login_server
  container_registry_username = azurerm_container_registry.main.admin_username
  
  container_registry_password_secret_id = azurerm_key_vault.secret.acr_password.id
  
  container_registry_image_name = "firewall-manager-backend:latest"
  container_registry_image_tag  = "latest"
  
  site_config {
    minimum_tls_version = "TLS1_2"
    http2_enabled       = true
    always_on           = true
    
    app_settings = {
      DATABASE_URL               = "postgresql+asyncpg://postgres@${azurerm_postgresql_flexible_server.main.fqdn}:5432/fw_portal"
      REDIS_URL                  = "redis://:${azurerm_redis_cache.main.primary_connection_string}"
      ENVIRONMENT                = var.environment
      DEBUG                      = "False"
    }
  }
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = {
    Environment = var.environment
  }
}

# Frontend App Service
resource "azurerm_linux_app_service" "frontend" {
  name                = "${var.environment}-frontend"
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id
  
  container_registry_login = azurerm_container_registry.main.login_server
  container_registry_username = azurerm_container_registry.main.admin_username
  
  container_registry_password_secret_id = azurerm_key_vault.secret.acr_password.id
  
  container_registry_image_name = "firewall-manager-frontend:latest"
  container_registry_image_tag  = "latest"
  
  site_config {
    minimum_tls_version = "TLS1_2"
    http2_enabled       = true
    always_on           = true
  }
  
  tags = {
    Environment = var.environment
  }
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = "${var.environment}acr"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Standard"
  admin_enabled       = true
  
  tags = {
    Environment = var.environment
  }
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "${var.environment}-appinsights"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  workspace_id        = azurerm_log_analytics_workspace.main.id
  type                = "web"
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.environment}-loganalytics"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGBV3"
  retention_in_days   = 30
}

output "backend_url" {
  value = "https://${azurerm_linux_app_service.backend.name}.azurewebsites.net"
}

output "frontend_url" {
  value = "https://${azurerm_linux_app_service.frontend.name}.azurewebsites.net"
}
```

### Task 6.6: Kubernetes Manifests (`kubernetes/`)

Create `kubernetes/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: firewall-manager-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: backend-secrets
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: default
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: firewall-manager-frontend:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: default
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: firewall-manager
  namespace: default
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: firewall-manager.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
```

Create `kubernetes/values.yaml`:

```yaml
# Helm values for firewall-manager
replicaCount: 2

image:
  repository: firewall-manager
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  hosts:
    - firewall-manager.example.com
  tls:
    - secretName: firewall-tls
      hosts:
        - firewall-manager.example.com

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
```

### Task 6.7: Update `backend/Dockerfile`

```dockerfile
# Build stage
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .
RUN mkdir -p /app/data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Task 6.8: Update `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build -- --configuration production

# Production stage
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget -q --spider http://localhost:80 || exit 1
CMD ["nginx", "-g", "daemon off;"]
```

## Acceptance Criteria

- [ ] CI pipeline runs backend lint, test, build
- [ ] CI pipeline runs frontend lint, test, build
- [ ] CD pipeline deploys to staging on develop branch
- [ ] CD pipeline requires approval for production
- [ ] Terraform creates all Azure resources
- [ ] Kubernetes manifests deploy to AKS
- [ ] Health checks configured for all services
- [ ] Autoscaling configured for production