"""
Activity Logging Service.

Provides utilities for automatically logging user activities
when orders, payments, and other actions are performed.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional
import json

from ..models import ActivityLog, ActivityAction


class ActivityLogService:
    """Service for recording user activities."""

    @staticmethod
    async def log(
        db: AsyncSession,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        description: Optional[str] = None,
        extra_data: Optional[dict] = None
    ) -> ActivityLog:
        """
        Log a user activity.

        Args:
            db: Database session
            user_id: ID of the user performing the action
            action: Action type (e.g., "CREATE_ORDER")
            entity_type: Type of entity affected (e.g., "order")
            entity_id: ID of the affected entity
            description: Human-readable description
            extra_data: Additional data as dictionary

        Returns:
            Created ActivityLog instance
        """
        log_entry = ActivityLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            extra_data=json.dumps(extra_data) if extra_data else None,
            created_at=datetime.utcnow()
        )
        db.add(log_entry)
        await db.flush()
        return log_entry

    @staticmethod
    async def log_order_created(
        db: AsyncSession,
        user_id: int,
        order_id: int,
        order_number: str,
        customer_name: str,
        total_price: float
    ) -> ActivityLog:
        """Log when an order is created."""
        return await ActivityLogService.log(
            db=db,
            user_id=user_id,
            action=ActivityAction.CREATE_ORDER.value,
            entity_type="order",
            entity_id=order_id,
            description=f"Created order {order_number} for {customer_name} (₱{total_price:.2f})",
            extra_data={
                "order_number": order_number,
                "customer_name": customer_name,
                "total_price": total_price
            }
        )

    @staticmethod
    async def log_order_cancelled(
        db: AsyncSession,
        user_id: int,
        order_id: int,
        order_number: str,
        cancelled_by: str = "user"
    ) -> ActivityLog:
        """Log when an order is cancelled."""
        return await ActivityLogService.log(
            db=db,
            user_id=user_id,
            action=ActivityAction.CANCEL_ORDER.value,
            entity_type="order",
            entity_id=order_id,
            description=f"Order {order_number} cancelled by {cancelled_by}",
            extra_data={
                "order_number": order_number,
                "cancelled_by": cancelled_by
            }
        )

    @staticmethod
    async def log_payment_uploaded(
        db: AsyncSession,
        user_id: int,
        order_id: int,
        order_number: str
    ) -> ActivityLog:
        """Log when a payment is uploaded."""
        return await ActivityLogService.log(
            db=db,
            user_id=user_id,
            action=ActivityAction.UPLOAD_PAYMENT.value,
            entity_type="payment",
            entity_id=order_id,
            description=f"Payment uploaded for order {order_number}",
            extra_data={
                "order_number": order_number
            }
        )

    @staticmethod
    async def log_payment_verified(
        db: AsyncSession,
        admin_user_id: int,
        order_id: int,
        order_number: str
    ) -> ActivityLog:
        """Log when a payment is verified (admin action)."""
        return await ActivityLogService.log(
            db=db,
            user_id=admin_user_id,
            action=ActivityAction.VERIFY_PAYMENT.value,
            entity_type="payment",
            entity_id=order_id,
            description=f"Payment verified for order {order_number}",
            extra_data={
                "order_number": order_number,
                "verified_by": "admin"
            }
        )

    @staticmethod
    async def log_order_status_change(
        db: AsyncSession,
        user_id: int,
        order_id: int,
        order_number: str,
        old_status: str,
        new_status: str
    ) -> ActivityLog:
        """Log when an order status changes."""
        return await ActivityLogService.log(
            db=db,
            user_id=user_id,
            action=ActivityAction.UPDATE_ORDER.value,
            entity_type="order",
            entity_id=order_id,
            description=f"Order {order_number} status changed from {old_status} to {new_status}",
            extra_data={
                "order_number": order_number,
                "old_status": old_status,
                "new_status": new_status
            }
        )

    @staticmethod
    async def log_admin_created(
        db: AsyncSession,
        created_by_user_id: int,
        new_admin_id: int,
        new_admin_username: str
    ) -> ActivityLog:
        """Log when a new admin account is created."""
        return await ActivityLogService.log(
            db=db,
            user_id=created_by_user_id,
            action=ActivityAction.ADMIN_CREATED.value,
            entity_type="user",
            entity_id=new_admin_id,
            description=f"Created new admin account: {new_admin_username}",
            extra_data={
                "new_admin_id": new_admin_id,
                "new_admin_username": new_admin_username,
                "created_by_user_id": created_by_user_id
            }
        )

    @staticmethod
    async def log_user_promoted(
        db: AsyncSession,
        promoted_by_user_id: int,
        promoted_user_id: int,
        promoted_username: str,
        promoted_by_username: str
    ) -> ActivityLog:
        """Log when a user is promoted to admin."""
        return await ActivityLogService.log(
            db=db,
            user_id=promoted_by_user_id,
            action=ActivityAction.USER_PROMOTED.value,
            entity_type="user",
            entity_id=promoted_user_id,
            description=f"Promoted user {promoted_username} to Admin",
            extra_data={
                "promoted_user_id": promoted_user_id,
                "promoted_username": promoted_username,
                "old_role": "salesman",
                "new_role": "admin",
                "promoted_by_user_id": promoted_by_user_id,
                "promoted_by_username": promoted_by_username
            }
        )

    @staticmethod
    async def log_user_status_change(
        db: AsyncSession,
        changed_by_user_id: int,
        target_user_id: int,
        target_username: str,
        new_status: str,
        changed_by_username: str
    ) -> ActivityLog:
        """Log when a user's status is changed (suspended/activated)."""
        action = ActivityAction.USER_ACTIVATED.value if new_status == "Active" else ActivityAction.USER_SUSPENDED.value
        description = f"Activated user {target_username}" if new_status == "Active" else f"Suspended user {target_username}"

        return await ActivityLogService.log(
            db=db,
            user_id=changed_by_user_id,
            action=action,
            entity_type="user",
            entity_id=target_user_id,
            description=description,
            extra_data={
                "target_user_id": target_user_id,
                "target_username": target_username,
                "new_status": new_status,
                "changed_by_user_id": changed_by_user_id,
                "changed_by_username": changed_by_username
            }
        )
