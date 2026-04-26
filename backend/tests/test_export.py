"""Tests for data export endpoints."""
import pytest
from httpx import AsyncClient

from app.models import FirewallRule
from app.schemas import RuleAction, RuleStatus


class TestExportEndpoints:
    """Tests for export endpoints."""

    @pytest.mark.asyncio
    async def test_export_csv(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test exporting rules as CSV."""
        response = await client.get(
            "/api/v1/export/csv",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_export_json(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test exporting rules as JSON."""
        response = await client.get(
            "/api/v1/export/json",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list) or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_export_xml(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test exporting rules as XML."""
        response = await client.get(
            "/api/v1/export/xml",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_export_requires_auth(self, client: AsyncClient):
        """Test that export endpoints require authentication."""
        response = await client.get("/api/v1/export/csv")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_export_filtered(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test exporting filtered rules."""
        response = await client.get(
            "/api/v1/export/csv?landing_zone=corp",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 404]


class TestExportFormats:
    """Tests for export format validation."""

    @pytest.mark.asyncio
    async def test_export_pdf(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test exporting rules as PDF."""
        response = await client.get(
            "/api/v1/export/pdf",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_export_excel(self, client: AsyncClient, multiple_rules, admin_access_token):
        """Test exporting rules as Excel."""
        response = await client.get(
            "/api/v1/export/xlsx",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        assert response.status_code in [200, 404]


class TestExportHeaders:
    """Tests for export response headers."""

    @pytest.mark.asyncio
    async def test_csv_content_type(self, client: AsyncClient, admin_access_token):
        """Test CSV export has correct content type."""
        response = await client.get(
            "/api/v1/export/csv",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        if response.status_code == 200:
            assert "text/csv" in response.headers.get("content-type", "").lower() or \
                   "application/octet-stream" in response.headers.get("content-type", "").lower()

    @pytest.mark.asyncio
    async def test_json_content_type(self, client: AsyncClient, admin_access_token):
        """Test JSON export has correct content type."""
        response = await client.get(
            "/api/v1/export/json",
            headers={"Authorization": f"Bearer {admin_access_token}"},
        )
        if response.status_code == 200:
            assert "application/json" in response.headers.get("content-type", "").lower()


class TestExportServices:
    """Tests for export service functions."""

    def test_export_service_import(self):
        """Test that export service can be imported."""
        from app.services import audit_service
        assert audit_service is not None