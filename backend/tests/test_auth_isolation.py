"""
Authentication and Isolation Tests (Test Auth_I).

Comprehensive tests for authentication and role-based data isolation.

Tests verify:
- Valid authentication is accepted
- Invalid/missing authentication is rejected
- Role-based access control (RBAC) enforcement
- Data isolation between salesmen
- Admin full access to all data
"""

import pytest
from httpx import AsyncClient

from app.models import User, Order, ActivityLog


@pytest.mark.asyncio
class TestAuthentication:
    """Authentication acceptance and rejection tests."""

    # ---- Valid Authentication ----

    async def test_admin_authentication_accepted(self, client: AsyncClient, admin_user):
        """Admin role authentication is accepted."""
        response = await client.get(
            "/products/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id)
            }
        )
        assert response.status_code == 200, (
            f"Admin auth should be accepted, got {response.status_code}"
        )

    async def test_salesman_authentication_accepted(self, client: AsyncClient, salesman_a):
        """Salesman role authentication is accepted."""
        response = await client.get(
            "/products/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )
        assert response.status_code == 200, (
            f"Salesman auth should be accepted, got {response.status_code}"
        )

    # ---- Invalid/Missing Authentication ----

    async def test_missing_role_header_rejected(self, client: AsyncClient):
        """Missing X-Simulated-Role header returns 401."""
        response = await client.get("/products/")
        assert response.status_code == 401, (
            f"Missing auth header should return 401, got {response.status_code}"
        )

    async def test_invalid_role_rejected(self, client: AsyncClient):
        """Invalid role value returns 401."""
        response = await client.get(
            "/products/",
            headers={"X-Simulated-Role": "superuser"}
        )
        assert response.status_code == 401, (
            f"Invalid role should return 401, got {response.status_code}"
        )

    async def test_empty_role_rejected(self, client: AsyncClient):
        """Empty role value returns 401."""
        response = await client.get(
            "/products/",
            headers={"X-Simulated-Role": ""}
        )
        assert response.status_code == 401, (
            f"Empty role should return 401, got {response.status_code}"
        )


@pytest.mark.asyncio
class TestRoleBasedAccessControl:
    """RBAC tests for admin-only endpoints."""

    # ---- User Management Access ----

    async def test_salesman_cannot_list_users(
        self, client: AsyncClient, salesman_a
    ):
        """Salesman cannot list users via /admin/users/."""
        response = await client.get(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )
        assert response.status_code in [401, 403], (
            f"Salesman accessing /admin/users/ should be rejected, got {response.status_code}"
        )

    async def test_admin_can_list_users(self, client: AsyncClient, admin_user):
        """Admin can list users."""
        response = await client.get(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id)
            }
        )
        assert response.status_code == 200, (
            f"Admin should access /admin/users/, got {response.status_code}"
        )

    # ---- Promo Code Access ----

    async def test_salesman_cannot_list_promos(self, client: AsyncClient, salesman_a):
        """Salesman cannot list promos via /admin/promo/."""
        response = await client.get(
            "/admin/promo/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )
        assert response.status_code in [401, 403], (
            f"Salesman accessing /admin/promo/ should be rejected, got {response.status_code}"
        )

    async def test_admin_can_list_promos(self, client: AsyncClient, admin_user):
        """Admin can list promo codes."""
        response = await client.get(
            "/admin/promo/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id)
            }
        )
        assert response.status_code == 200, (
            f"Admin should access /admin/promo/, got {response.status_code}"
        )

    # ---- Dashboard Access ----

    async def test_salesman_cannot_access_dashboard(self, client: AsyncClient, salesman_a):
        """Salesman cannot access dashboard summary."""
        response = await client.get(
            "/admin/dashboard/summary",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )
        assert response.status_code in [401, 403], (
            f"Salesman accessing dashboard should be rejected, got {response.status_code}"
        )

    async def test_admin_can_access_dashboard(self, client: AsyncClient, admin_user):
        """Admin can access dashboard summary."""
        response = await client.get(
            "/admin/dashboard/summary",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id)
            }
        )
        assert response.status_code == 200, (
            f"Admin should access dashboard, got {response.status_code}"
        )


@pytest.mark.asyncio
class TestSalesmanDataIsolation:
    """Test that salesmen are isolated from each other's data."""

    async def test_salesman_a_only_sees_own_orders(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_a_orders,
        salesman_b_orders
    ):
        """Salesman_A sees only their 3 orders, not Salesman_B's 2 orders."""
        response = await client.get(
            "/orders/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )
        assert response.status_code == 200
        orders = response.json()

        # Should see exactly 3 orders
        assert len(orders) == 3, (
            f"Salesman_A should see 3 orders, got {len(orders)}"
        )

        # Verify all orders belong to Salesman_A
        for order in orders:
            assert order["user_id"] == salesman_a.id, (
                f"Order {order['id']} should belong to Salesman_A"
            )

    async def test_salesman_b_only_sees_own_orders(
        self,
        client: AsyncClient,
        salesman_b,
        salesman_a_orders,
        salesman_b_orders
    ):
        """Salesman_B sees only their 2 orders, not Salesman_A's 3 orders."""
        response = await client.get(
            "/orders/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_b.id)
            }
        )
        assert response.status_code == 200
        orders = response.json()

        # Should see exactly 2 orders
        assert len(orders) == 2, (
            f"Salesman_B should see 2 orders, got {len(orders)}"
        )

        # Verify all orders belong to Salesman_B
        for order in orders:
            assert order["user_id"] == salesman_b.id, (
                f"Order {order['id']} should belong to Salesman_B"
            )

    async def test_salesman_a_cannot_access_salesman_b_order(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_b_orders
    ):
        """Salesman_A cannot access Salesman_B's order details."""
        other_order = salesman_b_orders[0]
        response = await client.get(
            f"/orders/{other_order.id}",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )
        assert response.status_code == 403, (
            f"Salesman_A accessing Salesman_B's order should be 403, got {response.status_code}"
        )

    async def test_salesman_a_only_sees_own_activity_logs(
        self,
        client: AsyncClient,
        salesman_a,
        activity_logs
    ):
        """Salesman_A sees only their own activity logs."""
        response = await client.get(
            "/activity-logs/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )
        assert response.status_code == 200
        data = response.json()
        logs = data.get("logs", [])

        # All logs should belong to Salesman_A
        for log in logs:
            assert log["user_id"] == salesman_a.id, (
                f"Log {log['id']} should belong to Salesman_A"
            )


@pytest.mark.asyncio
class TestAdminFullVisibility:
    """Test that admin sees all data in the system."""

    async def test_admin_sees_all_orders(
        self,
        client: AsyncClient,
        admin_user,
        salesman_a_orders,
        salesman_b_orders
    ):
        """Admin sees all 5 orders from both salesmen."""
        response = await client.get(
            "/orders/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id)
            }
        )
        assert response.status_code == 200
        orders = response.json()

        expected_count = len(salesman_a_orders) + len(salesman_b_orders)
        assert len(orders) == expected_count, (
            f"Admin should see {expected_count} orders, got {len(orders)}"
        )

    async def test_admin_sees_all_activity_logs(
        self,
        client: AsyncClient,
        admin_user,
        activity_logs
    ):
        """Admin sees all activity logs."""
        response = await client.get(
            "/activity-logs/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id)
            }
        )
        assert response.status_code == 200
        data = response.json()
        logs = data.get("logs", [])

        assert len(logs) == len(activity_logs), (
            f"Admin should see all {len(activity_logs)} logs"
        )

    async def test_admin_can_access_any_order(
        self,
        client: AsyncClient,
        admin_user,
        salesman_a_orders
    ):
        """Admin can access any salesman's order."""
        sales_order = salesman_a_orders[0]
        response = await client.get(
            f"/orders/{sales_order.id}",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id)
            }
        )
        assert response.status_code == 200, (
            f"Admin should access any order, got {response.status_code}"
        )


@pytest.mark.asyncio
class TestSecurityEnforcement:
    """Security edge cases and bypass prevention."""

    async def test_spoofing_admin_id_rejected(
        self,
        client: AsyncClient,
        salesman_a
    ):
        """Salesman cannot bypass RBAC by spoofing admin user ID."""
        response = await client.get(
            "/admin/users/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": "1",
                "X-Simulated-Username": "admin"
            }
        )
        assert response.status_code in [401, 403], (
            f"Spoofing admin ID should be rejected, got {response.status_code}"
        )

    async def test_unauthenticated_requests_rejected(self, client: AsyncClient):
        """Unauthenticated requests to protected endpoints return 401."""
        endpoints = [
            "/orders/",
            "/activity-logs/",
            "/admin/users/",
            "/admin/promo/",
        ]
        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 401, (
                f"Unauthenticated request to {endpoint} should return 401"
            )

    async def test_case_insensitive_role_matching(
        self,
        client: AsyncClient
    ):
        """Role matching should be case-insensitive."""
        # Test uppercase
        response = await client.get(
            "/products/",
            headers={"X-Simulated-Role": "ADMIN"}
        )
        assert response.status_code == 200, (
            "Uppercase role should be accepted"
        )

        # Test mixed case
        response = await client.get(
            "/products/",
            headers={"X-Simulated-Role": "Salesman"}
        )
        assert response.status_code == 200, (
            "Mixed-case role should be accepted"
        )


@pytest.mark.asyncio
class TestEndpointIsolation:
    """Isolation tests for specific endpoints."""

    async def test_orders_isolation(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_b
    ):
        """Orders endpoint respects user isolation."""
        # Salesman A's orders
        resp_a = await client.get(
            "/orders/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )
        orders_a = resp_a.json()
        ids_a = {o["id"] for o in orders_a}

        # Salesman B's orders
        resp_b = await client.get(
            "/orders/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_b.id)
            }
        )
        orders_b = resp_b.json()
        ids_b = {o["id"] for o in orders_b}

        # No overlap
        overlap = ids_a & ids_b
        assert len(overlap) == 0, (
            f"Orders should not overlap: found shared IDs: {overlap}"
        )

    async def test_activity_logs_isolation(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_b
    ):
        """Activity logs endpoint respects user isolation."""
        # Salesman A's logs
        resp_a = await client.get(
            "/activity-logs/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id)
            }
        )
        logs_a = resp_a.json()["logs"]
        user_ids_a = {log["user_id"] for log in logs_a}

        # Salesman B's logs
        resp_b = await client.get(
            "/activity-logs/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_b.id)
            }
        )
        logs_b = resp_b.json()["logs"]
        user_ids_b = {log["user_id"] for log in logs_b}

        # No cross-contamination
        assert all(uid == salesman_a.id for uid in user_ids_a), (
            "All logs for Salesman_A should have user_id == Salesman_A.id"
        )
        assert all(uid == salesman_b.id for uid in user_ids_b), (
            "All logs for Salesman_B should have user_id == Salesman_B.id"
        )
