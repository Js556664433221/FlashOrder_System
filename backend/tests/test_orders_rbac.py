"""
Tests for Role-Based Data Isolation on Order endpoints.

Verifies:
- Salesmen can ONLY see their own orders
- Admins can see ALL orders
- Salesmen cannot access other users' order details
- Data isolation is enforced at database query level
"""

import pytest
from httpx import AsyncClient

from app.models import Order, User
from tests.conftest import admin_headers, salesman_headers


@pytest.mark.asyncio
class TestOrdersDataIsolation:
    """Test data isolation on order endpoints."""

    async def test_admin_sees_all_orders(
        self,
        client: AsyncClient,
        admin_user,
        salesman_a_orders,
        salesman_b_orders
    ):
        """Admin should see ALL orders from all salesmen."""
        response = await client.get(
            "/orders/",
            headers=admin_headers(admin_user.id)
        )
        assert response.status_code == 200

        orders = response.json()
        # Admin should see all 5 orders (3 from A + 2 from B)
        assert len(orders) == 5

        # Verify both salesmen's orders are visible
        order_numbers = [o["order_number"] for o in orders]
        for order in salesman_a_orders:
            assert order.order_number in order_numbers
        for order in salesman_b_orders:
            assert order.order_number in order_numbers

    async def test_salesman_a_sees_only_own_orders(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_a_orders,
        salesman_b_orders
    ):
        """Salesman A should see ONLY their own orders."""
        response = await client.get(
            "/orders/",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 200

        orders = response.json()
        # Should see only 3 orders
        assert len(orders) == 3

        # Verify only Salesman A's orders are visible
        order_numbers = [o["order_number"] for o in orders]
        for order in salesman_a_orders:
            assert order.order_number in order_numbers

        # Verify Salesman B's orders are NOT visible
        for order in salesman_b_orders:
            assert order.order_number not in order_numbers

    async def test_salesman_b_sees_only_own_orders(
        self,
        client: AsyncClient,
        salesman_b,
        salesman_a_orders,
        salesman_b_orders
    ):
        """Salesman B should see ONLY their own orders."""
        response = await client.get(
            "/orders/",
            headers=salesman_headers(salesman_b.id, "salesman_b")
        )
        assert response.status_code == 200

        orders = response.json()
        # Should see only 2 orders
        assert len(orders) == 2

        # Verify only Salesman B's orders are visible
        order_numbers = [o["order_number"] for o in orders]
        for order in salesman_b_orders:
            assert order.order_number in order_numbers

        # Verify Salesman A's orders are NOT visible
        for order in salesman_a_orders:
            assert order.order_number not in order_numbers

    async def test_salesman_cannot_access_other_order_detail(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_b_orders
    ):
        """Salesman A should NOT be able to view Salesman B's order details."""
        # Try to access Salesman B's order
        other_order = salesman_b_orders[0]
        response = await client.get(
            f"/orders/{other_order.id}",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 403
        assert "access denied" in response.json()["detail"].lower()

    async def test_salesman_can_access_own_order_detail(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_a_orders
    ):
        """Salesman should be able to view their own order details."""
        own_order = salesman_a_orders[0]
        response = await client.get(
            f"/orders/{own_order.id}",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 200
        assert response.json()["order_number"] == own_order.order_number

    async def test_admin_can_access_any_order_detail(
        self,
        client: AsyncClient,
        admin_user,
        salesman_a_orders,
        salesman_b_orders
    ):
        """Admin should be able to view any order's details."""
        # Access Salesman A's order
        response = await client.get(
            f"/orders/{salesman_a_orders[0].id}",
            headers=admin_headers(admin_user.id)
        )
        assert response.status_code == 200

        # Access Salesman B's order
        response = await client.get(
            f"/orders/{salesman_b_orders[0].id}",
            headers=admin_headers(admin_user.id)
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestOrderReceiptAccess:
    """Test data isolation on receipt endpoint."""

    async def test_salesman_cannot_download_other_receipt(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_b_orders
    ):
        """Salesman should NOT be able to download another user's receipt."""
        other_order = salesman_b_orders[0]
        response = await client.get(
            f"/orders/{other_order.id}/receipt",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 403

    async def test_salesman_can_download_own_receipt(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_a_orders
    ):
        """Salesman should be able to download their own receipt."""
        own_order = salesman_a_orders[0]
        response = await client.get(
            f"/orders/{own_order.id}/receipt",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        # Should return PDF content
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")

    async def test_admin_can_download_any_receipt(
        self,
        client: AsyncClient,
        admin_user,
        salesman_a_orders,
        salesman_b_orders
    ):
        """Admin should be able to download any receipt."""
        # Download Salesman A's receipt
        response = await client.get(
            f"/orders/{salesman_a_orders[0].id}/receipt",
            headers=admin_headers(admin_user.id)
        )
        assert response.status_code == 200

        # Download Salesman B's receipt
        response = await client.get(
            f"/orders/{salesman_b_orders[0].id}/receipt",
            headers=admin_headers(admin_user.id)
        )
        assert response.status_code == 200


@pytest.mark.asyncio
class TestOrderCancellationAccess:
    """Test data isolation on order cancellation."""

    async def test_salesman_cannot_cancel_other_order(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_b_orders
    ):
        """Salesman should NOT be able to cancel another user's order."""
        other_order = salesman_b_orders[0]
        response = await client.post(
            f"/orders/{other_order.id}/request-cancel",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 403

    async def test_salesman_can_cancel_own_order(
        self,
        client: AsyncClient,
        salesman_a,
        salesman_a_orders
    ):
        """Salesman should be able to cancel their own order."""
        own_order = salesman_a_orders[0]
        response = await client.post(
            f"/orders/{own_order.id}/request-cancel",
            headers=salesman_headers(salesman_a.id, "salesman_a")
        )
        assert response.status_code == 200
        assert response.json()["status"] == "Cancel Requested"
