"""
Access Control Tests (Test C).

Verify RBAC enforcement on administrative endpoints:
- /admin/users (User Management)
- /admin/promo (Promo Code CRUD)

Test C: Salesmen MUST receive 403 Forbidden when accessing admin-only routes.
Test C: Admin MUST receive 200 OK when accessing admin routes.
"""

import pytest
from httpx import AsyncClient

from app.models import User


@pytest.mark.asyncio
class TestAdminEndpointAccessControl:
    """Test C: Verify RBAC enforcement on admin-only endpoints."""

    # =========================================================
    # User Management (/admin/users) Tests
    # =========================================================

    async def test_salesman_a_cannot_access_user_management_get(
        self,
        client: AsyncClient,
        salesman_a
    ):
        """
        Test C: Salesman_A attempts GET /admin/users.

        EXPECTED: 403 Forbidden (or 401 Unauthorized).
        Salesmen MUST NOT have access to User Management.
        """
        response = await client.get(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id),
                "X-Simulated-Username": "salesman_a"
            }
        )

        assert response.status_code in [401, 403], (
            f"Expected 401 or 403 Forbidden, got {response.status_code}. "
            f"Salesmen MUST NOT access /admin/users/"
        )

    async def test_salesman_b_cannot_access_user_management_get(
        self,
        client: AsyncClient,
        salesman_b
    ):
        """
        Test C: Salesman_B attempts GET /admin/users.

        EXPECTED: 403 Forbidden (or 401 Unauthorized).
        """
        response = await client.get(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_b.id),
                "X-Simulated-Username": "salesman_b"
            }
        )

        assert response.status_code in [401, 403], (
            f"Salesman should receive 401/403, got {response.status_code}"
        )

    async def test_admin_can_access_user_management_get(
        self,
        client: AsyncClient,
        admin_user
    ):
        """
        Test C: Admin attempts GET /admin/users.

        EXPECTED: 200 OK.
        Only Admin should successfully access User Management.
        """
        response = await client.get(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id),
                "X-Simulated-Username": "admin"
            }
        )

        assert response.status_code == 200, (
            f"Admin should receive 200 OK, got {response.status_code}"
        )

    async def test_salesman_a_cannot_create_user(
        self,
        client: AsyncClient,
        salesman_a
    ):
        """
        Test C: Salesman_A attempts POST /admin/users.

        EXPECTED: 403 Forbidden.
        Salesmen MUST NOT create users.
        """
        response = await client.post(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id),
                "X-Simulated-Username": "salesman_a"
            },
            json={
                "username": "new_test_user",
                "email": "new@test.com",
                "password": "test123",
                "role": "salesman"
            }
        )

        assert response.status_code in [401, 403], (
            f"Salesman should receive 401/403, got {response.status_code}"
        )

    async def test_admin_can_create_user(
        self,
        client: AsyncClient,
        admin_user
    ):
        """
        Test C: Admin attempts POST /admin/users.

        EXPECTED: 200 OK (or 201 Created).
        """
        response = await client.post(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id),
                "X-Simulated-Username": "admin"
            },
            json={
                "username": "new_admin_user",
                "email": "new_admin@test.com",
                "password": "test123",
                "role": "salesman"
            }
        )

        assert response.status_code in [200, 201], (
            f"Admin should receive 200/201, got {response.status_code}"
        )

    # =========================================================
    # Promo Code Management (/admin/promo) Tests
    # =========================================================

    async def test_salesman_a_cannot_access_promo_list(
        self,
        client: AsyncClient,
        salesman_a
    ):
        """
        Test C: Salesman_A attempts GET /admin/promo/.

        EXPECTED: 403 Forbidden (or 401 Unauthorized).
        Salesmen MUST NOT have access to Promo Code Management.
        """
        response = await client.get(
            "/admin/promo/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id),
                "X-Simulated-Username": "salesman_a"
            }
        )

        assert response.status_code in [401, 403], (
            f"Expected 401/403 Forbidden, got {response.status_code}. "
            f"Salesmen MUST NOT access /admin/promo/"
        )

    async def test_salesman_b_cannot_access_promo_list(
        self,
        client: AsyncClient,
        salesman_b
    ):
        """
        Test C: Salesman_B attempts GET /admin/promo/.

        EXPECTED: 403 Forbidden (or 401 Unauthorized).
        """
        response = await client.get(
            "/admin/promo/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_b.id),
                "X-Simulated-Username": "salesman_b"
            }
        )

        assert response.status_code in [401, 403], (
            f"Salesman should receive 401/403, got {response.status_code}"
        )

    async def test_admin_can_access_promo_list(
        self,
        client: AsyncClient,
        admin_user
    ):
        """
        Test C: Admin attempts GET /admin/promo/.

        EXPECTED: 200 OK.
        Only Admin should successfully access Promo Code Management.
        """
        response = await client.get(
            "/admin/promo/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id),
                "X-Simulated-Username": "admin"
            }
        )

        assert response.status_code == 200, (
            f"Admin should receive 200 OK, got {response.status_code}"
        )

    async def test_salesman_a_cannot_create_promo(
        self,
        client: AsyncClient,
        salesman_a
    ):
        """
        Test C: Salesman_A attempts POST /admin/promo/.

        EXPECTED: 403 Forbidden.
        Salesmen MUST NOT create promo codes.
        """
        response = await client.post(
            "/admin/promo/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id),
                "X-Simulated-Username": "salesman_a"
            },
            json={
                "code": "TESTCODE",
                "discount_type": "percentage",
                "value": 10.0,
                "is_active": True
            }
        )

        assert response.status_code in [401, 403], (
            f"Salesman should receive 401/403, got {response.status_code}"
        )

    async def test_admin_can_create_promo(
        self,
        client: AsyncClient,
        admin_user
    ):
        """
        Test C: Admin attempts POST /admin/promo/.

        EXPECTED: 200/201 OK.
        """
        response = await client.post(
            "/admin/promo/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id),
                "X-Simulated-Username": "admin"
            },
            json={
                "code": "ADMINTEST10",
                "discount_type": "percentage",
                "value": 10.0,
                "is_active": True
            }
        )

        assert response.status_code in [200, 201], (
            f"Admin should receive 200/201, got {response.status_code}"
        )

    # =========================================================
    # Admin Dashboard Tests
    # =========================================================

    async def test_salesman_cannot_access_dashboard(
        self,
        client: AsyncClient,
        salesman_a
    ):
        """
        Test C: Salesman attempts to access /admin/dashboard/summary.

        EXPECTED: 403 Forbidden.
        Dashboard is admin-only.
        """
        response = await client.get(
            "/admin/dashboard/summary",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )

        assert response.status_code in [401, 403], (
            f"Salesman should receive 401/403, got {response.status_code}"
        )

    async def test_admin_can_access_dashboard(
        self,
        client: AsyncClient,
        admin_user
    ):
        """
        Test C: Admin accesses /admin/dashboard/summary.

        EXPECTED: 200 OK.
        """
        response = await client.get(
            "/admin/dashboard/summary",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id)
            }
        )

        assert response.status_code == 200, (
            f"Admin should receive 200 OK, got {response.status_code}"
        )

    # =========================================================
    # Admin Products Tests
    # =========================================================

    async def test_salesman_cannot_access_admin_products(
        self,
        client: AsyncClient,
        salesman_a
    ):
        """
        Test C: Salesman attempts to access /admin/products.

        EXPECTED: 403 Forbidden.
        Admin products management is admin-only.
        """
        response = await client.get(
            "/admin/products",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )

        assert response.status_code in [401, 403], (
            f"Salesman should receive 401/403, got {response.status_code}"
        )

    async def test_admin_can_access_admin_products(
        self,
        client: AsyncClient,
        admin_user
    ):
        """
        Test C: Admin accesses /admin/products.

        EXPECTED: 200 OK.
        """
        response = await client.get(
            "/admin/products",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id)
            }
        )

        assert response.status_code == 200, (
            f"Admin should receive 200 OK, got {response.status_code}"
        )


@pytest.mark.asyncio
class TestAccessControlEnforcement:
    """Additional RBAC enforcement tests for completeness."""

    async def test_no_bypass_via_different_user_id(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_b
    ):
        """
        Verify that spoofing admin user ID doesn't bypass RBAC.

        Salesman_A tries to access admin endpoints by setting user ID to admin's ID.
        Should still be rejected because role is 'salesman'.
        """
        response = await client.get(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": "1",  # Trying to spoof admin
                "X-Simulated-Username": "admin"
            }
        )

        assert response.status_code in [401, 403], (
            f"RBAC should reject salesman role regardless of user ID, got {response.status_code}"
        )

    async def test_unauthenticated_request_rejected(
        self,
        client: AsyncClient
    ):
        """
        Verify that requests without authentication are rejected.
        """
        response = await client.get("/admin/users/")

        assert response.status_code == 401, (
            f"Unauthenticated request should return 401, got {response.status_code}"
        )

    async def test_invalid_role_rejected(
        self,
        client: AsyncClient
    ):
        """
        Verify that invalid roles are rejected.
        """
        response = await client.get(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "manager"  # Invalid role
            }
        )

        assert response.status_code == 401, (
            f"Invalid role should return 401, got {response.status_code}"
        )

    async def test_case_sensitive_role(
        self,
        client: AsyncClient,
        admin_user
    ):
        """
        Verify role matching is case-insensitive.
        """
        response = await client.get(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "ADMIN"  # Uppercase
            }
        )

        assert response.status_code == 200, (
            f"Uppercase role should be accepted, got {response.status_code}"
        )
