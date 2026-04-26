from pydantic_settings import BaseSettings
from pydantic import Field, model_validator
from typing import Optional, List
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


# ─── Domain Enums ──────────────────────────────────────────────────────────────


class RuleAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ALERT = "alert"


class RuleStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalLevel(str, Enum):
    SECURITY = "security"
    WORKLOAD = "workload"
    SECURITY_AND_WORKLOAD = "security_and_workload"


class ResourceCategory(str, Enum):
    NETWORK = "network"
    SECURITY = "security"
    APPLICATION = "application"
    DATA = "data"


class WorkloadType(str, Enum):
    WEB = "web"
    API = "api"
    DATABASE = "database"
    STORAGE = "storage"
    COMPUTE = "compute"
    AI = "ai"
    DATA_PROCESSING = "data_processing"


class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    REJECT = "reject"
    SUBMIT = "submit"
    VIEW = "view"


class Role(str, Enum):
    ADMIN = "admin"
    SECURITY_STAKEHOLDER = "security_stakeholder"
    WORKLOAD_STAKEHOLDER = "workload_stakeholder"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


# ─── Settings ──────────────────────────────────────────────────────────────────


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Azure Firewall Manager"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    # Database - use environment variables with defaults for local dev
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/firewall_manager",
        description="Database connection URL"
    )
    DATABASE_SSL_MODE: str = "prefer"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Azure Entra ID Configuration
    AZURE_TENANT_ID: str = Field(default="", description="Azure AD Tenant ID")
    AZURE_CLIENT_ID: str = Field(default="", description="Azure AD Client ID")
    AZURE_CLIENT_SECRET: str = Field(default="", description="Azure AD Client Secret")
    AZURE_INSTANCE_METADATA: str = "https://login.microsoftonline.com/common/.well-known/openid-configuration"

    # JWT Settings
    SECRET_KEY: str = Field(default="", description="JWT secret key - MUST be set in production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Origins
    CORS_ORIGINS: str = "http://localhost:4200,http://localhost:3000"

    # Security
    RATE_LIMIT_AUTH: str = "5/minute"  # Auth endpoint rate limit
    RATE_LIMIT_DEFAULT: str = "100/minute"
    REQUEST_ID_HEADER: str = "X-Request-ID"

    # Approval Workflow Settings
    DEFAULT_APPROVAL_LEVEL: ApprovalLevel = ApprovalLevel.SECURITY_AND_WORKLOAD
    AUTO_APPROVE_AFTER_DAYS: int = 30

    @property
    def allowed_cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode='after')
    def validate_production_settings(self):
        """Validate required settings for production."""
        if self.ENVIRONMENT == Environment.PRODUCTION:
            if not self.SECRET_KEY or self.SECRET_KEY == "dev-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be set in production")
            if not self.AZURE_TENANT_ID:
                raise ValueError("AZURE_TENANT_ID must be set in production")
            if not self.AZURE_CLIENT_ID:
                raise ValueError("AZURE_CLIENT_ID must be set in production")
        return self

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()