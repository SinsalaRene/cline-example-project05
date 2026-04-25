# Azure Firewall Rule Management Application

A comprehensive application for managing Azure firewall rules in large landing zones with:
- Audit and approval workflows
- Entra ID authentication
- Multi-level authorization roles
- Multi-level approval flows (workload stakeholder + security stakeholder)
- Containerized deployment on Azure
- Cloud-provider-agnostic architecture

## Project Structure

```
azure-firewall-manager/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── main.py          # Application entry point
│   │   ├── config.py        # Configuration settings
│   │   ├── database.py      # Database connection
│   │   ├── models.py        # Pydantic models
│   │   ├── dependencies.py  # DI & auth dependencies
│   │   ├── routers/         # API routes
│   │   ├── services/        # Business logic
│   │   ├── auth/            # Auth middleware & policies
│   │   └── workflows/       # Approval workflows
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # Angular frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/        # Core services & guards
│   │   │   ├── shared/      # Shared components
│   │   │   ├── features/    # Feature modules
│   │   │   └── environments/
│   │   ├── index.html
│   │   └── styles/
│   ├── angular.json
│   ├── package.json
│   └── Dockerfile
├── infrastructure/          # IaC for Azure
│   ├── bicep/
│   └── terraform/
├── docker-compose.yml
└── .gitignore
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Run Locally with Docker Compose
```bash
docker-compose up --build
```

## Architecture
- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** Angular 17+ with standalone components
- **Auth:** Azure Entra ID (OIDC + OAuth2)
- **Deployment:** Docker containers on Azure App Service / AKS
- **Database:** PostgreSQL (Azure Database for PostgreSQL)