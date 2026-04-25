from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from enum import Enum


class Environment(str):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ApprovalLevel(str, Enum):
    """Approval hierarchy levels for the multi-level approval workflow."""
    SECURITY = "security"
    WORKLOAD = "workload"
    SECURITY_AND_WORKLOAD = "security_and_workload"


class Role(str, Enum):
    """Multi-level authorization roles."""
    ADMIN = "admin"
    SECURITY_STAKEHOLDER = "security_stakeholder"
    WORKLOAD_STAKEHOLDER = "workload_stakeholder"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Azure Firewall Manager"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/firewall_manager"

    # Azure Entra ID Configuration
    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""
    AZURE_INSTANCE_METADATA: str = "https://login.microsoftonline.com/common/.well-known/openid-configuration"

    # JWT Settings
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Origins
    CORS_ORIGINS: str = "http://localhost:4200,http://localhost:3000"

    # Approval Workflow Settings
    DEFAULT_APPROVAL_LEVEL: ApprovalLevel = ApprovalLevel.SECURITY_AND_WORKLOAD
    AUTO_APPROVE_AFTER_DAYS: int = 30

    @property
    def allowed_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()