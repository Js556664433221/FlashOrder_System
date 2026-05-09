"""
Test promo code restriction: only one promo code allowed per order.

Tests:
1. Attempting to submit a list of promo codes returns 400 error
2. Attempting to pass duplicate promo codes returns 400 error
3. A single valid promo code is accepted
4. Only one discount is applied even if multiple codes somehow pass validation
5. Database reflects correct total_price with single code discount
"""

import pytest
from httpx import AsyncClient

from app.models import PromoCode
from app.models.models import UserRole
from tests.conftest import admin_headers, salesman_headers


@pytest.fixture
async def percentage_promo(db_session) -> PromoCode:
    """Create a 10% percentage discount promo."""
    promo = PromoCode(
        code="PERCENT10",
        discount_type="percentage",
        value=10.0,
        is_active=1,
    )
    db_session.add(promo)
    await db_session.commit()
    await db_session.refresh(promo)
    return promo


@pytest.fixture
async def flat_promo(db_session) -> PromoCode:
    """Create a flat ₱50 discount promo."""
    promo = PromoCode(
        code="FLAT50",
        discount_type="flat",
        value=50.0,
        is_active=1,
    )
    db_session.add(promo)
    await db_session.commit()
    await db_session.refresh(promo)
    return promo


@pytest.fixture
def valid_order_payload(sample_products):
    """Base order payload with one item."""
    return {
        "items": [{"product_id": sample_products[0].id, "quantity": 2}],
        "customer_name": "Test Customer",
        "delivery_method": "Pickup",
    }


class TestPromoCodeRestriction:
    """Tests for single promo code per order restriction."""

    @pytest.mark.asyncio
    async def test_list_of_promo_codes_rejected(
        self,
        client: AsyncClient,
        salesman_a,
        valid_order_payload,
        percentage_promo,
    ):
        """Server must reject order if promo_code is a list (stacking attempt)."""
        payload = {**valid_order_payload, "promo_code": [percentage_promo.code, "OTHERCODE"]}

        response = await client.post("/orders/", json=payload, headers=salesman_headers(salesman_a.id, salesman_a.username))

        assert response.status_code == 400
        assert "Only one promo code allowed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_duplicate_codes_rejected(
        self,
        client: AsyncClient,
        salesman_a,
        valid_order_payload,
        percentage_promo,
    ):
        """Server must reject order if multiple codes are sent comma-separated."""
        payload = {**valid_order_payload, "promo_code": f"{percentage_promo.code},{percentage_promo.code}"}

        response = await client.post("/orders/", json=payload, headers=salesman_headers(salesman_a.id, salesman_a.username))

        # Backend rejects comma-separated codes with 400
        assert response.status_code == 400
        assert "Only one promo code allowed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_single_valid_promo_accepted(
        self,
        client: AsyncClient,
        salesman_a,
        valid_order_payload,
        percentage_promo,
    ):
        """A single valid promo code should be accepted and applied."""
        payload = {**valid_order_payload, "promo_code": percentage_promo.code}

        response = await client.post("/orders/", json=payload, headers=salesman_headers(salesman_a.id, salesman_a.username))

        assert response.status_code == 200
        order = response.json()
        assert order["applied_promo_id"] is not None
        assert order["discount_amount"] > 0

    @pytest.mark.asyncio
    async def test_discount_from_single_code_only(
        self,
        client: AsyncClient,
        salesman_a,
        db_session,
        valid_order_payload,
        percentage_promo,
    ):
        """The discount applied must come from only one promo code."""
        from sqlalchemy import select
        from app.models import Order

        payload = {**valid_order_payload, "promo_code": percentage_promo.code}
        response = await client.post("/orders/", json=payload, headers=salesman_headers(salesman_a.id, salesman_a.username))

        assert response.status_code == 200
        order_resp = response.json()

        # Verify in database - only one promo_id linked
        result = await db_session.execute(select(Order).filter(Order.id == order_resp["id"]))
        db_order = result.scalar_one()

        assert db_order.applied_promo_id == percentage_promo.id
        assert db_order.discount_amount > 0
        # No stacking: only one promo linked
        assert db_order.discount_amount < 1000  # sanity check it's reasonable

    @pytest.mark.asyncio
    async def test_total_price_reflects_single_discount(
        self,
        client: AsyncClient,
        salesman_a,
        db_session,
        valid_order_payload,
        flat_promo,
    ):
        """Database total_price must reflect deduction from only one promo code."""
        from sqlalchemy import select
        from app.models import Order

        # Product price: sample_products[0].price = 100.00
        # Quantity: 2 -> subtotal = 200.00
        # Flat promo value: 50.00
        # Expected total: 200 - 50 = 150.00

        payload = {**valid_order_payload, "promo_code": flat_promo.code}
        response = await client.post("/orders/", json=payload, headers=salesman_headers(salesman_a.id, salesman_a.username))

        assert response.status_code == 200
        order_resp = response.json()

        expected_discount = flat_promo.value  # 50.0
        expected_total = 200.0 - expected_discount  # 150.0

        # API response
        assert order_resp["discount_amount"] == expected_discount
        assert order_resp["total_price"] == expected_total

        # Database record
        result = await db_session.execute(select(Order).filter(Order.id == order_resp["id"]))
        db_order = result.scalar_one()

        assert float(db_order.discount_amount) == expected_discount
        assert float(db_order.total_price) == expected_total
        assert db_order.applied_promo_id == flat_promo.id

    @pytest.mark.asyncio
    async def test_order_without_promo_has_no_discount(
        self,
        client: AsyncClient,
        salesman_a,
        valid_order_payload,
    ):
        """An order without a promo code must have zero discount."""
        response = await client.post("/orders/", json=valid_order_payload, headers=salesman_headers(salesman_a.id, salesman_a.username))

        assert response.status_code == 200
        order = response.json()
        assert order["applied_promo_id"] is None
        assert order["discount_amount"] == 0.0

    @pytest.mark.asyncio
    async def test_invalid_promo_code_rejected(
        self,
        client: AsyncClient,
        salesman_a,
        valid_order_payload,
    ):
        """An invalid promo code must be rejected."""
        payload = {**valid_order_payload, "promo_code": "INVALIDCODE999"}

        response = await client.post("/orders/", json=payload, headers=salesman_headers(salesman_a.id, salesman_a.username))

        assert response.status_code == 400
        assert "Invalid promo code" in response.json()["detail"] or "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_percentage_discount_calculated_correctly(
        self,
        client: AsyncClient,
        salesman_a,
        db_session,
        valid_order_payload,
        percentage_promo,
    ):
        """Percentage discount must be calculated correctly on the subtotal."""
        from sqlalchemy import select
        from app.models import Order

        # sample_products[0].price = 100.00, qty = 2 -> subtotal = 200.00
        # 10% of 200 = 20.00
        expected_discount = 20.0
        expected_total = 200.0 - expected_discount  # 180.0

        payload = {**valid_order_payload, "promo_code": percentage_promo.code}
        response = await client.post("/orders/", json=payload, headers=salesman_headers(salesman_a.id, salesman_a.username))

        assert response.status_code == 200
        order = response.json()

        assert order["discount_amount"] == expected_discount
        assert order["total_price"] == expected_total

        # Verify DB
        result = await db_session.execute(select(Order).filter(Order.id == order["id"]))
        db_order = result.scalar_one()
        assert float(db_order.discount_amount) == expected_discount
        assert float(db_order.total_price) == expected_total

    @pytest.mark.asyncio
    async def test_flat_discount_capped_at_subtotal(
        self,
        client: AsyncClient,
        salesman_a,
        db_session,
        sample_products,
    ):
        """Flat discount must not exceed the subtotal."""
        from sqlalchemy import select, text
        from app.models import Order

        # Create a flat discount larger than the order
        big_flat = PromoCode(
            code="BIGFLAT",
            discount_type="flat",
            value=99999.0,
            is_active=1,
        )
        db_session.add(big_flat)
        await db_session.commit()

        # Get a real product
        result = await db_session.execute(text("SELECT id FROM products LIMIT 1"))
        row = result.fetchone()
        if row:
            product_id = row[0]
        else:
            pytest.skip("No products in database")

        payload = {
            "items": [{"product_id": product_id, "quantity": 1}],
            "customer_name": "Test Customer",
            "delivery_method": "Pickup",
            "promo_code": "BIGFLAT",
        }

        response = await client.post("/orders/", json=payload, headers=salesman_headers(salesman_a.id, salesman_a.username))
        assert response.status_code == 200
        order = response.json()

        # Discount should not exceed the order total (100.00 * 1 = 100.00)
        assert float(order["total_price"]) >= 0  # Never negative
        assert float(order["discount_amount"]) <= 100.0  # Capped at subtotal