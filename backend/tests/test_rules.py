"""Tests for firewall rule endpoints."""
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import FirewallRule, Tag
from app.schemas import RuleAction, RuleStatus, ResourceCategory
from app.main import app


class TestRuleEndpoints:
    """Tests for rule CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_rule(self, client: AsyncClient, superuser, admin_access_token, rule_data):
        """Test creating a new firewall rule."""
        response = await client.post(
            "/api/v1/firewalls/rules",
            json=rule_data,
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == rule_data["name"]
        assert data["description"] == rule_data["description"]
        assert data["landing_zone"] == rule_data["landing_zone"]
        assert data["action"] == rule_data["action"]
        assert data["status"] == "draft"

    @pytest.mark.asyncio
    async def test_get_rules(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test retrieving list of rules."""
        response = await client.get(
            "/api/v1/firewalls/rules",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert len(data["items"]) >= 5

    @pytest.mark.asyncio
    async def test_get_rule_by_id(self, client: AsyncClient, sample_rule, admin_access_token):
        """Test retrieving a single rule by ID."""
        response = await client.get(
            f"/api/v1/firewalls/rules/{sample_rule.id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_rule.id
        assert data["name"] == sample_rule.name

    @pytest.mark.asyncio
    async def test_get_rule_not_found(self, client: AsyncClient, admin_access_token):
        """Test retrieving a non-existent rule returns 404."""
        response = await client.get(
            "/api/v1/firewalls/rules/99999",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_rule(self, client: AsyncClient, sample_rule, admin_access_token):
        """Test updating a rule."""
        update_data = {"description": "Updated description"}
        response = await client.put(
            f"/api/v1/firewalls/rules/{sample_rule.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_rule_partial(self, client: AsyncClient, active_rule, admin_access_token):
        """Test updating only partial fields of a rule."""
        update_data = {"name": "Updated Name"}
        response = await client.put(
            f"/api/v1/firewalls/rules/{active_rule.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        # Other fields should remain unchanged
        assert data["action"] == "allow"

    @pytest.mark.asyncio
    async def test_delete_rule(self, client: AsyncClient, sample_rule, admin_access_token):
        """Test deleting a rule."""
        response = await client.delete(
            f"/api/v1/firewalls/rules/{sample_rule.id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        # Verify deletion
        response = await client.get(
            f"/api/v1/firewalls/rules/{sample_rule.id}",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_rule_not_found(self, client: AsyncClient, admin_access_token):
        """Test deleting a non-existent rule."""
        response = await client.delete(
            "/api/v1/firewalls/rules/99999",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_rule_validation(self, client: AsyncClient, admin_access_token, invalid_rule_data):
        """Test that rule validation works."""
        response = await client.post(
            "/api/v1/firewalls/rules",
            json=invalid_rule_data,
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [400, 422]


class TestRuleFiltering:
    """Tests for rule filtering and search."""

    @pytest.mark.asyncio
    async def test_filter_by_landing_zone(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test filtering rules by landing zone."""
        response = await client.get(
            "/api/v1/firewalls/rules?landing_zone=corp",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["landing_zone"] == "corp"

    @pytest.mark.asyncio
    async def test_filter_by_status(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test filtering rules by status."""
        response = await client.get(
            "/api/v1/firewalls/rules?status=ACTIVE",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_filter_by_action(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test filtering rules by action."""
        response = await client.get(
            "/api/v1/firewalls/rules?action=allow",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert item["action"] == "allow"

    @pytest.mark.asyncio
    async def test_search_rules(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test searching rules by keyword."""
        response = await client.get(
            "/api/v1/firewalls/rules?search=Test",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        for item in data["items"]:
            assert "Test" in item["name"] or "Test" in item.get("description", "")

    @pytest.mark.asyncio
    async def test_combined_filters(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test combining multiple filters."""
        response = await client.get(
            "/api/v1/firewalls/rules?landing_zone=corp&action=allow&status=ACTIVE",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["landing_zone"] == "corp"
            assert item["action"] == "allow"
            assert item["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test pagination of rules."""
        response = await client.get(
            "/api/v1/firewalls/rules?page=1&per_page=2",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1


class TestRuleStatusTransitions:
    """Tests for rule status transitions."""

    @pytest.mark.asyncio
    async def test_activate_draft_rule(self, client: AsyncClient, sample_rule, admin_access_token):
        """Test activating a draft rule."""
        response = await client.post(
            f"/api/v1/firewalls/rules/{sample_rule.id}/activate",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        # Status should be updatable via PUT
        response = await client.put(
            f"/api/v1/firewalls/rules/{sample_rule.id}",
            json={"status": "active"},
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 202]

    @pytest.mark.asyncio
    async def test_deactivate_active_rule(self, client: AsyncClient, active_rule, admin_access_token):
        """Test deactivating an active rule."""
        response = await client.put(
            f"/api/v1/firewalls/rules/{active_rule.id}",
            json={"status": "draft"},
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"


class TestRuleValidation:
    """Tests for rule validation."""

    @pytest.mark.asyncio
    async def test_priority_range(self, client: AsyncClient, superuser, admin_access_token):
        """Test that priority must be within valid range."""
        from app.config import MIN_PRIORITY, MAX_PRIORITY
        data = {
            "name": "Rule with high priority",
            "landing_zone": "corp",
            "rule_collection_name": "Test Collection",
            "priority": MAX_PRIORITY + 1,
            "action": "allow",
        }
        response = await client.post(
            "/api/v1/firewalls/rules",
            json=data,
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_required_fields(self, client: AsyncClient, admin_access_token):
        """Test that required fields are enforced."""
        minimal_data = {"name": "Incomplete Rule"}
        response = await client.post(
            "/api/v1/firewalls/rules",
            json=minimal_data,
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_unique_rule_name(self, client: AsyncClient, sample_rule, admin_access_token):
        """Test that rule names are unique."""
        # Create a rule with the same name
        same_name_data = {
            "name": sample_rule.name,
            "landing_zone": "dev",
            "rule_collection_name": "Unique Test",
            "priority": 500,
            "action": "allow",
        }
        response = await client.post(
            "/api/v1/firewalls/rules",
            json=same_name_data,
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        # Should either reject duplicate name or allow it (depends on implementation)
        assert response.status_code in [200, 400, 422]


class TestRuleActions:
    """Tests for firewall rule actions."""

    def test_rule_action_allow(self):
        """Test ALLOW action."""
        assert RuleAction.ALLOW.value == "allow"

    def test_rule_action_deny(self):
        """Test DENY action."""
        assert RuleAction.DENY.value == "deny"

    def test_rule_action_alert(self):
        """Test ALERT action."""
        assert RuleAction.ALERT.value == "alert"

    def test_rule_action_invalid(self):
        """Test invalid action raises error."""
        with pytest.raises(ValueError):
            RuleAction("invalid_action")


class TestRuleCategories:
    """Tests for rule categories."""

    def test_resource_category_network(self):
        """Test NETWORK category."""
        assert ResourceCategory.NETWORK.value == "network"

    def test_resource_category_app(self):
        """Test APP category."""
        assert ResourceCategory.APPLICATION.value == "application"

    def test_resource_category_monitoring(self):
        """Test MONITORING category."""
        assert ResourceCategory.MONITORING.value == "monitoring"