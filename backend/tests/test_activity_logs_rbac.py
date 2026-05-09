"""
Tests for Role-Based Data Isolation on Activity Logs endpoints.

Verifies:
- Salesmen can ONLY see their own activity logs
- Admins can see ALL activity logs
- Filtering works correctly for both roles
- Pagination respects data isolation
"""

import pytest
from httpx import AsyncClient

from app.models import ActivityLog, User
from tests.conftest import admin_headers, salesman_headers


@pytest.mark.asyncio
class TestActivityLogsDataIsolation:
    """Test data isolation on activity logs endpoints."""

    async def test_admin_sees_all_activity_logs(
        self,
        client: AsyncClient,
        admin_user,
        activity_logs,
        salesman_a,
        salesman_b
    ):
        """Admin should see ALL activity logs from all users."""
        response = await client.get(
            "/activity-logs/",
            headers=admin_headers(admin_user.id)
        )
        assert response.status_code == 200

        data = response.json()
        assert "logs" in data
        logs = data["logs"]

        # Admin should see all 5 logs (3 from A + 2 from B)
        assert len(logs) == 5

        # Verify both salesmen's logs are visible
        user_ids = {log["user_id"] for log in logs}
        assert salesman_a.id in user_ids
        assert salesman_b.id in user_ids

    async def test_salesman_a_sees_only_own_logs(
        self,
        client: AsyncClient,
        salesman_a,
        activity_logs,
        salesman_b
    ):
        """Salesman A should see ONLY their own activity logs."""
        response = await client.get(
            "/activity-logs/",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 200

        data = response.json()
        assert "logs" in data
        logs = data["logs"]

        # Should see only 3 logs (Salesman A's orders)
        assert len(logs) == 3

        # Verify all logs belong to Salesman A
        for log in logs:
            assert log["user_id"] == salesman_a.id

        # Verify no logs from Salesman B
        assert not any(log["user_id"] == salesman_b.id for log in logs)

    async def test_salesman_b_sees_only_own_logs(
        self,
        client: AsyncClient,
        salesman_b,
        activity_logs,
        salesman_a
    ):
        """Salesman B should see ONLY their own activity logs."""
        response = await client.get(
            "/activity-logs/",
            headers=salesman_headers(salesman_b.id, "salesman_b")
        )
        assert response.status_code == 200

        data = response.json()
        logs = data["logs"]

        # Should see only 2 logs (Salesman B's orders)
        assert len(logs) == 2

        # Verify all logs belong to Salesman B
        for log in logs:
            assert log["user_id"] == salesman_b.id

        # Verify no logs from Salesman A
        assert not any(log["user_id"] == salesman_a.id for log in logs)

    async def test_total_count_respects_isolation(
        self,
        client: AsyncClient,
        salesman_a,
        activity_logs
    ):
        """Total count should respect data isolation."""
        response = await client.get(
            "/activity-logs/",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 200

        data = response.json()
        # Total should match visible logs count
        assert data["total"] == len(data["logs"])
        assert data["total"] == 3


@pytest.mark.asyncio
class TestActivityLogsFiltering:
    """Test filtering on activity logs respects data isolation."""

    async def test_action_filter_with_isolation(
        self,
        client: AsyncClient,
        salesman_a,
        activity_logs
    ):
        """Action filter should work within data isolation."""
        response = await client.get(
            "/activity-logs/",
            params={"action": "CREATE_ORDER"},
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 200

        logs = response.json()["logs"]
        # Salesman A should still only see their own filtered logs
        assert len(logs) == 3
        for log in logs:
            assert log["user_id"] == salesman_a.id
            assert log["action"] == "CREATE_ORDER"

    async def test_entity_type_filter_with_isolation(
        self,
        client: AsyncClient,
        salesman_a,
        activity_logs
    ):
        """Entity type filter should work within data isolation."""
        response = await client.get(
            "/activity-logs/",
            params={"entity_type": "order"},
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 200

        logs = response.json()["logs"]
        # Salesman A should still only see their own filtered logs
        assert len(logs) == 3
        for log in logs:
            assert log["user_id"] == salesman_a.id
            assert log["entity_type"] == "order"

    async def test_pagination_with_isolation(
        self,
        client: AsyncClient,
        salesman_a,
        activity_logs
    ):
        """Pagination should respect data isolation."""
        # Get first page
        response = await client.get(
            "/activity-logs/",
            params={"limit": 2, "offset": 0},
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["logs"]) == 2
        # Total should still be 3 (all of Salesman A's logs)
        assert data["total"] == 3

        # Get second page
        response = await client.get(
            "/activity-logs/",
            params={"limit": 2, "offset": 2},
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["logs"]) == 1
        assert data["total"] == 3


@pytest.mark.asyncio
class TestActivityLogsSummary:
    """Test activity summary respects data isolation."""

    async def test_admin_summary_shows_all(
        self,
        client: AsyncClient,
        admin_user,
        activity_logs,
        salesman_a,
        salesman_b
    ):
        """Admin summary should show all activity counts."""
        response = await client.get(
            "/activity-logs/summary",
            headers=admin_headers(admin_user.id)
        )
        assert response.status_code == 200

        data = response.json()
        assert data["user_role"] == "admin"
        assert data["filtered_by_user"] is False
        # Should show all activity
        assert data["total_today"] == 5

    async def test_salesman_summary_shows_only_own(
        self,
        client: AsyncClient,
        salesman_a,
        activity_logs
    ):
        """Salesman summary should show only their activity counts."""
        response = await client.get(
            "/activity-logs/summary",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 200

        data = response.json()
        assert data["user_role"] == "salesman"
        assert data["filtered_by_user"] is True
        # Should show only Salesman A's activity
        assert data["total_today"] == 3


@pytest.mark.asyncio
class TestOrderIsolationEnforcement:
    """Verify isolation is enforced at database query level."""

    async def test_no_cross_contamination(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_b,
        salesman_a_orders,
        salesman_b_orders,
        activity_logs
    ):
        """Ensure no data cross-contamination between users."""
        # Salesman A's orders
        a_response = await client.get(
            "/orders/",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        a_orders = a_response.json()
        a_order_ids = {o["id"] for o in a_orders}

        # Salesman B's orders
        b_response = await client.get(
            "/orders/",
            headers=salesman_headers(salesman_b.id, "salesman_b")
        )
        b_orders = b_response.json()
        b_order_ids = {o["id"] for o in b_orders}

        # Salesman A's logs
        a_logs_response = await client.get(
            "/activity-logs/",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        a_logs = a_logs_response.json()["logs"]
        a_log_entity_ids = {log.get("entity_id") for log in a_logs}

        # Salesman B's logs
        b_logs_response = await client.get(
            "/activity-logs/",
            headers=salesman_headers(salesman_b.id, "salesman_b")
        )
        b_logs = b_logs_response.json()["logs"]
        b_log_entity_ids = {log.get("entity_id") for log in b_logs}

        # No overlap in orders
        assert len(a_order_ids & b_order_ids) == 0

        # Salesman A's logs reference only Salesman A's orders
        for entity_id in a_log_entity_ids:
            if entity_id is not None:
                assert entity_id in a_order_ids or entity_id not in (o.id for o in salesman_b_orders)

        # Salesman B's logs reference only Salesman B's orders
        for entity_id in b_log_entity_ids:
            if entity_id is not None:
                assert entity_id in b_order_ids or entity_id not in (o.id for o in salesman_a_orders)
