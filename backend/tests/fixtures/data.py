"""Test data fixtures for backend tests."""
from app.config import RuleAction, RuleStatus, ResourceCategory, ApprovalStatus
from datetime import datetime, timezone


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
        "source_address": "0.0.0.0/0",
        "destination_address": "10.0.0.0/8",
        "destination_fqdns": ["*.example.com"],
        "protocols": ["TCP"],
        "workload": "web-frontend",
        "tags": ["production"],
    }


def sample_rule_data_deny():
    """Return sample deny firewall rule data."""
    return {
        "name": "Deny SSH Outbound",
        "description": "Block SSH outbound traffic",
        "landing_zone": "corp",
        "rule_collection_name": "Security Rules",
        "priority": 50,
        "action": "deny",
        "destination_ports": ["22"],
        "category": "network",
        "environment": "production",
        "source_address": "10.0.0.0/8",
        "destination_address": "0.0.0.0/0",
        "protocols": ["TCP"],
        "workload": "backend-service",
    }


def sample_rule_data_alert():
    """Return sample alert firewall rule data."""
    return {
        "name": "Alert on ICMP",
        "description": "Alert on ICMP traffic",
        "landing_zone": "dev",
        "rule_collection_name": "Monitoring Rules",
        "priority": 200,
        "action": "alert",
        "category": "monitoring",
        "environment": "staging",
    }


def sample_users():
    """Return sample users."""
    return [
        {
            "oidc_sub": "user-1-admin",
            "email": "admin@example.com",
            "display_name": "Admin User",
            "role": "admin",
            "is_active": True,
        },
        {
            "oidc_sub": "user-2-security",
            "email": "security@example.com",
            "display_name": "Security User",
            "role": "security_stakeholder",
            "is_active": True,
        },
        {
            "oidc_sub": "user-3-workload",
            "email": "workload@example.com",
            "display_name": "Workload User",
            "role": "workload_stakeholder",
            "is_active": True,
        },
        {
            "oidc_sub": "user-4-viewer",
            "email": "viewer@example.com",
            "display_name": "Viewer User",
            "role": "viewer",
            "is_active": False,
        },
    ]


def sample_approval_data():
    """Return sample approval data."""
    return {
        "action": "approve",
        "notes": "Approved for production",
    }


def sample_approval_reject_data():
    """Return sample reject approval data."""
    return {
        "action": "reject",
        "notes": "Security review required",
    }


def sample_tags():
    """Return sample tags data."""
    return [
        {"name": "production", "color": "#ff0000"},
        {"name": "staging", "color": "#ffaa00"},
        {"name": "development", "color": "#00ff00"},
        {"name": "testing", "color": "#0000ff"},
    ]


def sample_stats_data():
    """Return expected stats data."""
    return {
        "total_rules": 10,
        "rules_by_status": {
            "DRAFT": 3,
            "ACTIVE": 5,
            "DELETED": 2,
        },
        "rules_by_action": {
            "allow": 6,
            "deny": 3,
            "alert": 1,
        },
        "rules_by_landing_zone": {
            "corp": 7,
            "dev": 3,
        },
    }


def create_sample_firewall_rule(overrides=None):
    """Create a sample FirewallRule model object."""
    data = {
        "name": "Default Rule",
        "description": "Default test rule",
        "landing_zone": "corp",
        "rule_collection_name": "Default Collection",
        "priority": 500,
        "action": RuleAction.ALLOW,
        "status": RuleStatus.DRAFT,
        "source_address": "0.0.0.0/0",
        "destination_address": "10.0.0.0/8",
        "destination_ports": ["443"],
        "destination_fqdns": ["*.example.com"],
        "protocols": ["TCP"],
        "category": ResourceCategory.NETWORK,
        "workload": "web-service",
        "environment": "production",
        "is_enabled": True,
    }
    if overrides:
        data.update(overrides)
    return data


def create_sample_user(overrides=None):
    """Create a sample User model data."""
    data = {
        "oidc_sub": "test-user-sub",
        "email": "test@example.com",
        "display_name": "Test User",
        "role": "admin",
        "is_active": True,
    }
    if overrides:
        data.update(overrides)
    return data


def create_sample_approval_record(overrides=None):
    """Create a sample ApprovalRecord data."""
    data = {
        "rule_id": 1,
        "user_id": 1,
        "action": ApprovalStatus.APPROVE,
        "notes": "Test approval",
        "created_at": datetime.now(timezone.utc),
    }
    if overrides:
        data.update(overrides)
    return data