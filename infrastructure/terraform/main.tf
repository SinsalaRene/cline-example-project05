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

# Data source for Azure AD client config
data "azurerm_client_config" "current" {}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                        = "${var.environment}-kv"
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_enabled         = true
  purge_protection_enabled    = true
  sku_name                    = "Standard"

  access_policy {
    object_id   = data.azurerm_client_config.current.object_id
    tenant_id   = data.azurerm_client_config.current.tenant_id
    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover"
    ]
  }
}

# Azure Container Registry
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

# Key Vault Secret for ACR password
resource "azurerm_key_vault_secret" "acr_password" {
  name         = "acr-password"
  value        = azurerm_container_registry.main.admin_password
  key_vault_id = azurerm_key_vault.main.id
}

# Backend App Service
resource "azurerm_linux_app_service" "backend" {
  name                = "${var.environment}-backend"
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  container_registry_login = azurerm_container_registry.main.login_server
  container_registry_username = azurerm_container_registry.main.admin_username

  container_registry_password_secret_id = azurerm_key_vault_secret.acr_password.id

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

  container_registry_password_secret_id = azurerm_key_vault_secret.acr_password.id

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