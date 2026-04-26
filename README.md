# Azure Firewall Rule Management Application

A comprehensive application for managing Azure firewall rules in large landing zones with:
- Audit and approval workflows
- Entra ID authentication
- Multi-level authorization roles
- Multi-level approval flows (workload stakeholder + security stakeholder)
- Containerized deployment on Azure
- Cloud-provider-agnostic architecture

## Cline AI Generation and Local Configs

### Specs

- Intel(R) Core(TM) i7-8700K CPU @ 3.70GHz, 3696 MHz
- 32GB Ram 
- WSL Uses 20GB RAM
- GeForce 4070 TI Super (16GB VRAM)

### Llama.cpp

First generation done with this setup:
```bash
./build/bin/llama-server \
  -m /mnt/k/LLM-MODELS/Qwen3.6-35B-A3B-UD-IQ3_S.gguf  \
  --alias "qwen3-coder-30b" \
  -c 163840 \
  -ngl 999 \
  --n-cpu-moe 22 \
  --flash-attn on \
  --cache-type-k q4_0 \
  --cache-type-v q4_0 \
  -b 512 \
  -ub 512 \
  --jinja \
  -t 8 \
  --no-mmap \
  --host 0.0.0.0 \
  --port 8080
```

At the end of the genereation the system and the wsl itself almost crashed. 
Task got completed but I realized that this was to slow, unstable and ineffiecient. 

After many optimizations and benchmarks i used this command to generate the optimization plan:

```bash
./build/bin/llama-server \
  -m /mnt/c/LLM-MODELS/Qwen3.6-35B-A3B-UD-IQ3_S.gguf \
  --alias "qwen3.6-35b" \
  -c 163840 \
  -ngl 999 \
  --n-cpu-moe 2 \
  --flash-attn on \
  --cache-type-k q4_0 \
  --cache-type-v q4_0 \
  -b 1024 \
  -ub 1024 \
  -t 24 \
  --jinja \
  --no-mmap \
  --host 0.0.0.0 \
  --port 8080
```

Latest prompt eval:
```bash
prompt eval time =     747.23 ms /  1579 tokens (    0.47 ms per token,  2113.13 tokens per second)
       eval time =   24070.39 ms /  1350 tokens (   17.83 ms per token,    56.09 tokens per second)
      total time =   24817.62 ms /  2929 tokens
```

On my system that produced 3x the performance/speed. 

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

## Configuration

Copy `.env.example` to `.env` and configure the values:

```bash
cp .env.example .env
```

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SECRET_KEY` | JWT signing key | Yes |
| `AZURE_TENANT_ID` | Azure AD Tenant ID (production) | Yes |
| `AZURE_CLIENT_ID` | Azure AD Client ID (production) | Yes |
| `AZURE_CLIENT_SECRET` | Azure AD Client Secret (production) | Yes |
