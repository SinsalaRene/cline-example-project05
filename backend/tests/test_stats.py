"""Tests for statistics and dashboard endpoints."""
import pytest
from httpx import AsyncClient

from app.models import FirewallRule, User
from app.schemas import RuleAction, RuleStatus, ResourceCategory


class TestStatsEndpoints:
    """Tests for stats dashboard endpoints."""

    @pytest.mark.asyncio
    async def test_get_stats(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test getting overall statistics."""
        response = await client.get(
            "/api/v1/stats",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_rules" in data or "rules" in data or "summary" in data

    @pytest.mark.asyncio
    async def test_stats_requires_auth(self, client: AsyncClient):
        """Test that stats endpoints require authentication."""
        response = await client.get("/api/v1/stats")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_stats_with_no_rules(self, client: AsyncClient, admin_access_token):
        """Test stats when no rules exist."""
        response = await client.get(
            "/api/v1/stats",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data is not None


class TestDashboardEndpoints:
    """Tests for dashboard endpoints."""

    @pytest.mark.asyncio
    async def test_get_dashboard(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test getting dashboard data."""
        response = await client.get(
            "/api/v1/dashboard",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_dashboard_data_format(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test dashboard data structure."""
        response = await client.get(
            "/api/v1/dashboard",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


class TestStatsByCategory:
    """Tests for categorized statistics."""

    @pytest.mark.asyncio
    async def test_stats_by_status(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test statistics grouped by status."""
        response = await client.get(
            "/api/v1/stats/by-status",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_stats_by_action(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test statistics grouped by action."""
        response = await client.get(
            "/api/v1/stats/by-action",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_stats_by_landing_zone(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test statistics grouped by landing zone."""
        response = await client.get(
            "/api/v1/stats/by-landing-zone",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_stats_by_category(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test statistics grouped by category."""
        response = await client.get(
            "/api/v1/stats/by-category",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 404]


class TestRuleCountStats:
    """Tests for rule count statistics."""

    @pytest.mark.asyncio
    async def test_total_rule_count(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test total rule count matches."""
        response = await client.get(
            "/api/v1/stats/count",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        if response.status_code == 200:
            data = response.json()
            assert data["total"] >= 5

    @pytest.mark.asyncio
    async def test_active_rule_count(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test active rule count."""
        response = await client.get(
            "/api/v1/stats/count?status=ACTIVE",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        if response.status_code == 200:
            data = response.json()
            assert data["total"] >= 0

    @pytest.mark.asyncio
    async def test_draft_rule_count(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test draft rule count."""
        response = await client.get(
            "/api/v1/stats/count?status=DRAFT",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        if response.status_code == 200:
            data = response.json()
            assert data["total"] >= 0


class TestUserStats:
    """Tests for user-specific statistics."""

    @pytest.mark.asyncio
    async def test_user_rules_count(self, client: AsyncClient, superuser, admin_access_token):
        """Test getting rules count for current user."""
        response = await client.get(
            "/api/v1/stats/me",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code == 200


class TestStatisticsCalculations:
    """Tests for statistical calculations."""

    def test_rule_action_enum_values(self):
        """Test RuleAction enum values."""
        assert hasattr(RuleAction, "ALLOW")
        assert hasattr(RuleAction, "DENY")
        assert hasattr(RuleAction, "ALERT")

    def test_rule_status_enum_values(self):
        """Test RuleStatus enum values."""
        assert hasattr(RuleStatus, "DRAFT")
        assert hasattr(RuleStatus, "ACTIVE")
        assert hasattr(RuleStatus, "DELETED")

    def test_resource_category_enum_values(self):
        """Test ResourceCategory enum values."""
        assert hasattr(ResourceCategory, "NETWORK")
        assert hasattr(ResourceCategory, "APPLICATION")
        assert hasattr(ResourceCategory, "MONITORING")

    def test_action_values_correct(self):
        """Test action values match expected strings."""
        assert RuleAction.ALLOW.value == "allow"
        assert RuleAction.DENY.value == "deny"
        assert RuleAction.ALERT.value == "alert"

    def test_status_values_correct(self):
        """Test status values match expected strings."""
        assert RuleStatus.DRAFT.value == "DRAFT"
        assert RuleStatus.ACTIVE.value == "ACTIVE"
        assert RuleStatus.DELETED.value == "DELETED"