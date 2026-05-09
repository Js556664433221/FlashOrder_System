"""
Comprehensive Data Visibility Tests.

These tests verify that role-based data isolation is correctly enforced:
- Salesmen can ONLY see their own data
- Admins can see ALL data in the system

Test A: Salesman Isolation - Verify Salesman_A only sees their own orders
Test B: Admin Visibility - Verify Admin sees all orders
Activity Log Check: Verify activity logs follow the same isolation rules
"""

import pytest
from httpx import AsyncClient

from app.models import Order, User, ActivityLog


@pytest.mark.asyncio
class TestDataVisibilityOrders:
    """Test A & B: Data visibility on /orders endpoint."""

    async def test_a_salesman_a_isolation_only_sees_own_orders(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_a_orders,
        salesman_b_orders
    ):
        """
        Test A: Salesman Isolation.

        Verify that when authenticated as Salesman_A:
        - Response contains ONLY the 3 orders created by Salesman_A
        - Response contains ZERO orders from Salesman_B
        - Total count is exactly 3
        """
        response = await client.get(
            "/orders/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id),
                "X-Simulated-Username": "salesman_a"
            }
        )

        assert response.status_code == 200, "Request should succeed"

        orders = response.json()
        order_numbers = [o["order_number"] for o in orders]
        order_ids = [o["id"] for o in orders]
        user_ids = {o["user_id"] for o in orders}

        # Verify only Salesman_A's orders are present
        salesman_a_order_numbers = {o.order_number for o in salesman_a_orders}
        salesman_b_order_numbers = {o.order_number for o in salesman_b_orders}

        # Count verification
        assert len(orders) == 3, (
            f"Expected exactly 3 orders for Salesman_A, got {len(orders)}"
        )

        # All orders must belong to Salesman_A
        assert all(uid == salesman_a.id for uid in user_ids), (
            f"All orders should belong to Salesman_A (id={salesman_a.id}), "
            f"but found user_ids: {user_ids}"
        )

        # Salesman_A's orders are present
        for order in salesman_a_orders:
            assert order.order_number in order_numbers, (
                f"Order {order.order_number} from Salesman_A should be visible"
            )

        # Salesman_B's orders are NOT present
        for order in salesman_b_orders:
            assert order.order_number not in order_numbers, (
                f"Order {order.order_number} from Salesman_B should NOT be visible to Salesman_A"
            )

    async def test_b_admin_visibility_sees_all_orders(
        self,
        client: AsyncClient,
        admin_user,
        salesman_a_orders,
        salesman_b_orders
    ):
        """
        Test B: Admin Visibility.

        Verify that when authenticated as Admin:
        - Response contains ALL 5 orders from the system
        - Both Salesman_A's 3 orders and Salesman_B's 2 orders are visible
        - Total count is exactly 5
        """
        response = await client.get(
            "/orders/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id),
                "X-Simulated-Username": "admin"
            }
        )

        assert response.status_code == 200, "Request should succeed"

        orders = response.json()
        order_numbers = [o["order_number"] for o in orders]

        # Total count verification
        expected_total = len(salesman_a_orders) + len(salesman_b_orders)
        assert len(orders) == expected_total, (
            f"Expected {expected_total} orders total, got {len(orders)}"
        )

        # Verify both salesmen's orders are present
        for order in salesman_a_orders:
            assert order.order_number in order_numbers, (
                f"Admin should see Salesman_A's order: {order.order_number}"
            )

        for order in salesman_b_orders:
            assert order.order_number in order_numbers, (
                f"Admin should see Salesman_B's order: {order.order_number}"
            )

    async def test_salesman_b_isolation_verification(
        self,
        client: AsyncClient,
        salesman_b,
        salesman_a_orders,
        salesman_b_orders
    ):
        """
        Additional verification: Salesman_B isolation.

        Verify that when authenticated as Salesman_B:
        - Response contains ONLY the 2 orders created by Salesman_B
        - Response contains ZERO orders from Salesman_A
        """
        response = await client.get(
            "/orders/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_b.id),
                "X-Simulated-Username": "salesman_b"
            }
        )

        assert response.status_code == 200

        orders = response.json()
        order_numbers = [o["order_number"] for o in orders]

        # Verify count
        assert len(orders) == 2, (
            f"Salesman_B should see exactly 2 orders, got {len(orders)}"
        )

        # Verify only Salesman_B's orders
        for order in salesman_b_orders:
            assert order.order_number in order_numbers

        # Verify Salesman_A's orders are NOT present
        for order in salesman_a_orders:
            assert order.order_number not in order_numbers, (
                f"Salesman_B should NOT see Salesman_A's order: {order.order_number}"
            )


@pytest.mark.asyncio
class TestDataVisibilityActivityLogs:
    """Activity Log Check: Verify activity logs follow same isolation rules."""

    async def test_salesman_a_activity_log_isolation(
        self,
        client: AsyncClient,
        salesman_a,
        activity_logs,
        salesman_b
    ):
        """
        Activity Log Check: Salesman_A isolation.

        Verify that when authenticated as Salesman_A:
        - Response contains ONLY the activity logs created by Salesman_A
        - Response contains ZERO logs from Salesman_B
        """
        response = await client.get(
            "/activity-logs/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id),
                "X-Simulated-Username": "salesman_a"
            }
        )

        assert response.status_code == 200

        data = response.json()
        logs = data.get("logs", [])

        # All logs should belong to Salesman_A
        for log in logs:
            assert log["user_id"] == salesman_a.id, (
                f"Salesman_A should only see their own logs, "
                f"but found log with user_id={log['user_id']}"
            )

        # No logs should belong to Salesman_B
        for log in logs:
            assert log["user_id"] != salesman_b.id, (
                f"Salesman_A should NOT see Salesman_B's logs"
            )

    async def test_salesman_b_activity_log_isolation(
        self,
        client: AsyncClient,
        salesman_b,
        activity_logs,
        salesman_a
    ):
        """
        Activity Log Check: Salesman_B isolation.

        Verify that when authenticated as Salesman_B:
        - Response contains ONLY the activity logs created by Salesman_B
        - Response contains ZERO logs from Salesman_A
        """
        response = await client.get(
            "/activity-logs/",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_b.id),
                "X-Simulated-Username": "salesman_b"
            }
        )

        assert response.status_code == 200

        data = response.json()
        logs = data.get("logs", [])

        # All logs should belong to Salesman_B
        for log in logs:
            assert log["user_id"] == salesman_b.id, (
                f"Salesman_B should only see their own logs, "
                f"but found log with user_id={log['user_id']}"
            )

        # No logs should belong to Salesman_A
        for log in logs:
            assert log["user_id"] != salesman_a.id, (
                f"Salesman_B should NOT see Salesman_A's logs"
            )

    async def test_admin_activity_log_visibility(
        self,
        client: AsyncClient,
        admin_user,
        activity_logs,
        salesman_a,
        salesman_b
    ):
        """
        Activity Log Check: Admin visibility.

        Verify that when authenticated as Admin:
        - Response contains ALL activity logs from the system
        - Both Salesman_A's and Salesman_B's logs are visible
        """
        response = await client.get(
            "/activity-logs/",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id),
                "X-Simulated-Username": "admin"
            }
        )

        assert response.status_code == 200

        data = response.json()
        logs = data.get("logs", [])

        # Admin should see all logs
        user_ids_in_logs = {log["user_id"] for log in logs}

        assert salesman_a.id in user_ids_in_logs, (
            "Admin should see Salesman_A's activity logs"
        )
        assert salesman_b.id in user_ids_in_logs, (
            "Admin should see Salesman_B's activity logs"
        )


@pytest.mark.asyncio
class TestDataVisibilityOrderDetails:
    """Additional tests for order detail access."""

    async def test_salesman_cannot_view_other_order_details(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_b_orders
    ):
        """
        Verify Salesman_A cannot view Salesman_B's order details.

        Attempting to access another user's order should return 403 Forbidden.
        """
        # Try to access Salesman_B's first order
        order_to_access = salesman_b_orders[0]

        response = await client.get(
            f"/orders/{order_to_access.id}",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id),
                "X-Simulated-Username": "salesman_a"
            }
        )

        assert response.status_code == 403, (
            f"Expected 403 Forbidden when accessing another user's order, "
            f"got {response.status_code}"
        )

        assert "access denied" in response.json()["detail"].lower(), (
            "Error message should indicate access denied"
        )

    async def test_admin_can_view_any_order_detail(
        self,
        client: AsyncClient,
        admin_user,
        salesman_a_orders,
        salesman_b_orders
    ):
        """
        Verify Admin can view any order's details.

        Admin should successfully access both salesmen's orders.
        """
        # Access Salesman_A's order
        response_a = await client.get(
            f"/orders/{salesman_a_orders[0].id}",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id),
            }
        )
        assert response_a.status_code == 200

        # Access Salesman_B's order
        response_b = await client.get(
            f"/orders/{salesman_b_orders[0].id}",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id),
            }
        )
        assert response_b.status_code == 200


@pytest.mark.asyncio
class TestDataVisibilitySummary:
    """Summary/aggregate data visibility tests."""

    async def test_salesman_summary_only_counts_own_data(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_a_orders,
        salesman_b_orders
    ):
        """
        Verify salesman's summary endpoint only counts their own data.
        """
        response = await client.get(
            "/activity-logs/summary",
            headers={
                "X-Simulated-Role": "salesman",
                "X-Simulated-User-Id": str(salesman_a.id),
                "X-Simulated-Username": "salesman_a"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify summary is filtered
        assert data.get("filtered_by_user") is True, (
            "Salesman's summary should indicate filtered data"
        )
        assert data.get("user_role") == "salesman"

    async def test_admin_summary_counts_all_data(
        self,
        client: AsyncClient,
        admin_user,
        activity_logs
    ):
        """
        Verify admin's summary endpoint counts all data in the system.
        """
        response = await client.get(
            "/activity-logs/summary",
            headers={
                "X-Simulated-Role": "admin",
                "X-Simulated-User-Id": str(admin_user.id),
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify summary is NOT filtered
        assert data.get("filtered_by_user") is False, (
            "Admin's summary should NOT indicate filtered data"
        )
        assert data.get("user_role") == "admin"
