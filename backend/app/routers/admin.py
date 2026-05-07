from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid

from ..database import get_db
from ..models import Product, Order, OrderItem, Payment, OrderStatusEnum
from ..schemas import (
    AdminProductCreate, AdminProductUpdate, AdminProductResponse,
    AdminOrderUpdate, AdminOrderResponse, AdminPaymentResponse,
    AdminOrderStatus, AdminPaymentStatus, OrderItemWithProduct,
    VerifyPaymentRequest, VerifyPaymentResponse,
    RestockRequest, RestockResponse, DashboardSummaryResponse, LowStockProduct,
    ForceCancelResponse
)
from ..services import StockReservationService
from ..auth.dependencies import get_current_active_admin, MockUser

router = APIRouter(prefix="/admin", tags=["admin"])

LOW_STOCK_THRESHOLD = 10


def get_stock_status(order_status: str) -> str:
    """Determine stock status based on order status."""
    if order_status in (
        OrderStatusEnum.PENDING_PAYMENT.value,
        OrderStatusEnum.PAYMENT_UNDER_REVIEW.value,
        AdminOrderStatus.PENDING.value,
    ):
        return "Reserved"
    elif order_status in (
        OrderStatusEnum.PAID.value,
        AdminOrderStatus.COMPLETED.value,
        AdminOrderStatus.SHIPPED.value,
        AdminPaymentStatus.VERIFIED.value,
    ):
        return "Deducted"
    elif order_status in (
        OrderStatusEnum.CANCELLED.value,
        AdminOrderStatus.CANCELLED.value,
        AdminPaymentStatus.REJECTED.value,
    ):
        return "Released"
    return "Unknown"


def generate_sku() -> str:
    """Generate a unique SKU."""
    return f"SKU-{uuid.uuid4().hex[:8].upper()}"


def build_admin_order_response(order: Order) -> AdminOrderResponse:
    """Helper to build AdminOrderResponse from an Order."""
    items_with_product = [
        OrderItemWithProduct(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            product_name=item.product.name if item.product else "Unknown",
            product=AdminProductResponse(
                id=item.product.id,
                sku=item.product.sku,
                name=item.product.name,
                description=item.product.description,
                stock_balance=item.product.physical_stock - item.product.reserved_stock,
                price=item.product.price,
                version=item.product.version
            ),
            stock_status=get_stock_status(order.status)
        )
        for item in order.items
    ]

    payment_data = None
    if order.payments:
        latest_payment = max(order.payments, key=lambda p: p.uploaded_at)
        payment_data = AdminPaymentResponse(
            id=latest_payment.id,
            order_id=latest_payment.order_id,
            receipt_url=latest_payment.receipt_url,
            uploaded_at=latest_payment.uploaded_at
        )

    return AdminOrderResponse(
        id=order.id,
        order_number=order.order_number,
        total_price=order.total_price,
        status=order.status,
        created_at=order.created_at,
        items=items_with_product,
        payment=payment_data
    )


@router.post("/products", response_model=AdminProductResponse)
async def create_product(
    product_data: AdminProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_admin)
):
    """Add a new product to the inventory."""
    sku = generate_sku()
    product = Product(
        sku=sku,
        name=product_data.name,
        description=product_data.description,
        physical_stock=product_data.stock_quantity,
        reserved_stock=0,
        price=product_data.price,
        version=1
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=AdminProductResponse)
async def update_product(
    product_id: int,
    product_data: AdminProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_admin)
):
    """Update product details or adjust stock levels."""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product_data.name is not None:
        product.name = product_data.name
    if product_data.description is not None:
        product.description = product_data.description
    if product_data.price is not None:
        product.price = product_data.price
    if product_data.stock_quantity is not None:
        product.physical_stock = product_data.stock_quantity

    product.version += 1

    await db.commit()
    await db.refresh(product)
    return product


@router.get("/orders", response_model=list[AdminOrderResponse])
async def list_all_orders(
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_admin)
):
    """Fetch all orders with associated items and payment details."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [build_admin_order_response(order) for order in orders]


@router.get("/orders/{order_id}", response_model=AdminOrderResponse)
async def get_order_details(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_admin)
):
    """Fetch a specific order's full details including payment proof and item list."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return build_admin_order_response(order)


@router.patch("/orders/{order_id}", response_model=AdminOrderResponse)
async def update_order(
    order_id: int,
    order_data: AdminOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_admin)
):
    """Update order fulfillment status and/or payment status."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order_data.status is not None:
        new_status = order_data.status.value
    elif order_data.payment_status is not None:
        new_status = order_data.payment_status.value
    else:
        new_status = None

    if new_status is not None:
        order.status = new_status

    # STOCK DEDUCTION LOGIC - Admin only
    if new_status in (AdminPaymentStatus.VERIFIED.value, AdminOrderStatus.COMPLETED.value):
        for item in order.items:
            committed = await StockReservationService.commit_reservation(
                db, item.product_id, item.quantity
            )
            if not committed:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to commit stock for product {item.product_id}"
                )
    elif new_status == AdminOrderStatus.CANCELLED.value:
        for item in order.items:
            released = await StockReservationService.release_stock(
                db, item.product_id, item.quantity
            )
            if not released:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to release stock for product {item.product_id}"
                )

    await db.commit()

    # Reload order with relationships
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one()
    return build_admin_order_response(order)


@router.patch("/orders/{order_id}/verify", response_model=VerifyPaymentResponse)
async def verify_payment(
    order_id: int,
    verify_data: VerifyPaymentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_admin)
):
    """Admin endpoint to verify payment receipts. Approve = deduct stock, Reject = release stock."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.payments)
        )
        .filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.PAYMENT_UNDER_REVIEW.value:
        raise HTTPException(
            status_code=400,
            detail=f"Order is not under review. Current status: {order.status}"
        )

    if verify_data.action == "approve":
        order.status = OrderStatusEnum.PAID.value
        for item in order.items:
            committed = await StockReservationService.commit_reservation(
                db, item.product_id, item.quantity
            )
            if not committed:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to deduct stock for product {item.product_id}"
                )
        await db.commit()
        return VerifyPaymentResponse(
            order_id=order.id, order_number=order.order_number, status=order.status,
            action="approve", message="Payment verified. Stock deducted.", stock_action="deducted"
        )

    elif verify_data.action == "reject":
        order.status = OrderStatusEnum.CANCELLED.value
        for item in order.items:
            released = await StockReservationService.release_stock(
                db, item.product_id, item.quantity
            )
            if not released:
                await db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to release stock for product {item.product_id}"
                )
        await db.commit()
        return VerifyPaymentResponse(
            order_id=order.id, order_number=order.order_number, status=order.status,
            action="reject", message="Payment rejected. Stock released.", stock_action="released"
        )

    raise HTTPException(status_code=400, detail="Invalid action. Use 'approve' or 'reject'.")


@router.post("/inventory/restock", response_model=RestockResponse)
async def restock_inventory(
    restock_data: RestockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_admin)
):
    """Admin endpoint to add stock using atomic increment."""
    result = await db.execute(select(Product).filter(Product.id == restock_data.product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if restock_data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    previous_stock = product.physical_stock

    success = await StockReservationService.restock(db, restock_data.product_id, restock_data.quantity)
    if not success:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to restock")

    await db.refresh(product)

    return RestockResponse(
        product_id=product.id, sku=product.sku, name=product.name,
        previous_stock=previous_stock, added_quantity=restock_data.quantity,
        new_stock=product.physical_stock
    )


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_admin)
):
    """Admin endpoint providing global dashboard summary with order stats and low-stock alerts."""
    orders_result = await db.execute(select(Order))
    all_orders = orders_result.scalars().all()

    total_orders = len(all_orders)
    pending_payments = sum(1 for o in all_orders if o.status == OrderStatusEnum.PENDING_PAYMENT.value)
    paid_orders = sum(1 for o in all_orders if o.status == OrderStatusEnum.PAID.value)
    cancelled_orders = sum(1 for o in all_orders if o.status == OrderStatusEnum.CANCELLED.value)

    products_result = await db.execute(select(Product))
    all_products = products_result.scalars().all()

    low_stock_alerts = [
        LowStockProduct(
            id=p.id, sku=p.sku, name=p.name,
            physical_stock=p.physical_stock, reserved_stock=p.reserved_stock,
            available_stock=p.physical_stock - p.reserved_stock,
            threshold=LOW_STOCK_THRESHOLD
        )
        for p in all_products if (p.physical_stock - p.reserved_stock) <= LOW_STOCK_THRESHOLD
    ]

    total_revenue = sum(o.total_price for o in all_orders if o.status == OrderStatusEnum.PAID.value)

    return DashboardSummaryResponse(
        total_orders=total_orders, pending_payments=pending_payments,
        paid_orders=paid_orders, cancelled_orders=cancelled_orders,
        low_stock_alerts=low_stock_alerts, total_revenue=total_revenue
    )


@router.post("/orders/{order_id}/cancel", response_model=ForceCancelResponse)
async def force_cancel_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_admin)
):
    """
    Admin endpoint to force cancel an order.
    Releases reserved stock back to available inventory atomically.
    """
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Cannot cancel already cancelled or completed orders
    if order.status == OrderStatusEnum.CANCELLED.value:
        raise HTTPException(status_code=400, detail="Order is already cancelled")

    if order.status == OrderStatusEnum.PAID.value:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel a paid order. Process a refund instead."
        )

    # Release stock for all order items atomically
    failed_products = await StockReservationService.release_order_stock(db, list(order.items))

    if failed_products:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to release stock for products: {failed_products}"
        )

    # Update order status to cancelled
    order.status = OrderStatusEnum.CANCELLED.value

    await db.commit()

    return ForceCancelResponse(
        order_id=order.id,
        order_number=order.order_number,
        status=order.status,
        message="Order cancelled successfully. Stock has been released.",
        stock_released=True
    )


@router.post("/orders/{order_id}/approve-cancel", response_model=ForceCancelResponse)
async def approve_cancel_request(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: MockUser = Depends(get_current_active_admin)
):
    """
    Admin endpoint to approve a staff's cancel request.
    Releases reserved stock and sets order to cancelled.
    """
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).filter(Order.id == order_id)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatusEnum.CANCEL_REQUESTED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Order is not in cancel requested status. Current: {order.status}"
        )

    # Release stock for all order items atomically
    failed_products = await StockReservationService.release_order_stock(db, list(order.items))

    if failed_products:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to release stock for products: {failed_products}"
        )

    # Update order status to cancelled
    order.status = OrderStatusEnum.CANCELLED.value

    await db.commit()

    return ForceCancelResponse(
        order_id=order.id,
        order_number=order.order_number,
        status=order.status,
        message="Cancel request approved. Order cancelled and stock released.",
        stock_released=True
    )