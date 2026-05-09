"""
Tests for authentication and role-based access control.

Verifies:
- Valid role headers are accepted
- Invalid roles are rejected
- Missing authentication returns 401
- Inactive users are rejected (if applicable)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthentication:
    """Test authentication mechanisms."""

    async def test_admin_role_accepted(self, client: AsyncClient):
        """Admin role should be accepted."""
        response = await client.get(
            "/products/",
            headers={"X-Simulated-Role": "admin"}
        )
        # Should not return 401 Unauthorized
        assert response.status_code != 401

    async def test_salesman_role_accepted(self, client: AsyncClient):
        """Salesman role should be accepted."""
        response = await client.get(
            "/products/",
            headers={"X-Simulated-Role": "salesman"}
        )
        # Should not return 401 Unauthorized
        assert response.status_code != 401

    async def test_missing_role_returns_401(self, client: AsyncClient):
        """Missing X-Simulated-Role header should return 401."""
        response = await client.get("/products/")
        assert response.status_code == 401
        assert "authentication" in response.json()["detail"].lower()

    async def test_invalid_role_returns_401(self, client: AsyncClient):
        """Invalid role should return 401."""
        response = await client.get(
            "/products/",
            headers={"X-Simulated-Role": "invalid_role"}
        )
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_case_insensitive_role(self, client: AsyncClient):
        """Role should be case-insensitive."""
        response = await client.get(
            "/products/",
            headers={"X-Simulated-Role": "ADMIN"}
        )
        # Should accept uppercase role
        assert response.status_code != 401

    async def test_user_id_header_works(self, client: AsyncClient):
        """Custom user ID header should work."""
        response = await client.get(
            "/products/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": "99"
            }
        )
        assert response.status_code != 401


@pytest.mark.asyncio
class TestRoleBasedAccess:
    """Test role-based access control on various endpoints."""

    async def test_admin_only_endpoint_rejects_salesman(
        self,
        client: AsyncClient,
        admin_user
    ):
        """Admin-only endpoints should reject salesman role."""
        response = await client.get(
            "/admin/products",
            headers={"X-Simulated-Role": "salesman", "X-Simulated-User-Id": "2"}
        )
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    async def test_admin_only_endpoint_accepts_admin(
        self,
        client: AsyncClient,
        admin_user
    ):
        """Admin-only endpoints should accept admin role."""
        response = await client.get(
            "/admin/products",
            headers={"X-Simulated-Role": "admin", "X-Simulated-User-Id": "1"}
        )
        # Should not return 403 Forbidden
        assert response.status_code != 403

    async def test_shared_endpoint_accepts_salesman(
        self,
        client: AsyncClient,
        salesman_a
    ):
        """Shared endpoints should accept salesman role."""
        response = await client.get(
            "/products/",
            headers={"X-Simulated-Role": "salesman", "X-Simulated-User-Id": str(salesman_a.id)}
        )
        assert response.status_code == 200

    async def test_promo_crud_rejects_salesman(
        self,
        client: AsyncClient,
        salesman_a
    ):
        """Promo CRUD should reject salesman."""
        response = await client.get(
            "/admin/promo/",
            headers={"X-Simulated-Role": "salesman", "X-Simulated-User-Id": str(salesman_a.id)}
        )
        assert response.status_code == 403

    async def test_users_crud_rejects_salesman(
        self,
        client: AsyncClient,
        salesman_a
    ):
        """User CRUD should reject salesman."""
        response = await client.get(
            "/admin/users/",
            headers={"X-Simulated-Role": "salesman", "X-Simulated-User-Id": str(salesman_a.id)}
        )
        assert response.status_code == 403
