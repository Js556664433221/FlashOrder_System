from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


class StockReservationService:
    """Service for atomic stock reservation operations."""

    @staticmethod
    async def reserve_stock(
        db: AsyncSession,
        product_id: int,
        quantity: int
    ) -> bool:
        """
        Atomically reserve stock for a product.

        Uses conditional UPDATE to only increment reserved_stock if
        (physical_stock - reserved_stock) >= requested_quantity.

        Returns True if reservation succeeded, False if insufficient stock.
        """
        result = await db.execute(
            text("""
                UPDATE products
                SET reserved_stock = reserved_stock + :qty,
                    version = version + 1
                WHERE id = :product_id
                AND (physical_stock - reserved_stock) >= :qty
            """),
            {"product_id": product_id, "qty": quantity}
        )
        await db.flush()
        return result.rowcount > 0

    @staticmethod
    async def release_stock(
        db: AsyncSession,
        product_id: int,
        quantity: int
    ) -> bool:
        """
        Release previously reserved stock (e.g., order cancellation).

        Decrements reserved_stock only if reserved_stock >= quantity.
        """
        result = await db.execute(
            text("""
                UPDATE products
                SET reserved_stock = reserved_stock - :qty,
                    version = version + 1
                WHERE id = :product_id
                AND reserved_stock >= :qty
            """),
            {"product_id": product_id, "qty": quantity}
        )
        await db.flush()
        return result.rowcount > 0

    @staticmethod
    async def commit_reservation(
        db: AsyncSession,
        product_id: int,
        quantity: int
    ) -> bool:
        """
        Commit a reservation by decrementing both physical_stock and reserved_stock.

        Called when order is confirmed/shipped to convert reserved stock to actual deduction.
        """
        result = await db.execute(
            text("""
                UPDATE products
                SET physical_stock = physical_stock - :qty,
                    reserved_stock = reserved_stock - :qty,
                    version = version + 1
                WHERE id = :product_id
                AND physical_stock >= :qty
                AND reserved_stock >= :qty
            """),
            {"product_id": product_id, "qty": quantity}
        )
        await db.flush()
        return result.rowcount > 0

    @staticmethod
    async def restock(
        db: AsyncSession,
        product_id: int,
        quantity: int
    ) -> bool:
        """
        Atomically increment physical_stock for restocking.

        Uses conditional UPDATE to only increment physical_stock if quantity > 0.
        """
        if quantity <= 0:
            return False

        result = await db.execute(
            text("""
                UPDATE products
                SET physical_stock = physical_stock + :qty,
                    version = version + 1
                WHERE id = :product_id
            """),
            {"product_id": product_id, "qty": quantity}
        )
        await db.flush()
        return result.rowcount > 0

    @staticmethod
    async def release_order_stock(
        db: AsyncSession,
        order_items: list
    ) -> list:
        """
        Release stock for all items in an order.
        Used when cancelling an order to return reserved items to available inventory.

        Returns list of failed product_ids if any releases failed.
        """
        failed_products = []
        for item in order_items:
            success = await StockReservationService.release_stock(
                db, item.product_id, item.quantity
            )
            if not success:
                failed_products.append(item.product_id)
        return failed_products
