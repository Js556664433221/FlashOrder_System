"""
Activity Logs Router.

Provides endpoints for viewing activity logs with role-based data isolation:
- Salesmen can ONLY see their own activity logs
- Admins can see ALL activity logs in the system
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..models import ActivityLog, UserRole
from ..auth.dependencies import get_current_salesman_or_admin, CurrentUser

router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])


class ActivityLogResponse(BaseModel):
    """Response schema for a single activity log entry."""
    id: int
    user_id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    description: Optional[str] = None
    extra_data: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedActivityLogsResponse(BaseModel):
    """Response schema for paginated activity logs."""
    total: int
    logs: List[ActivityLogResponse]


@router.get("/", response_model=PaginatedActivityLogsResponse)
async def list_activity_logs(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_salesman_or_admin),
    limit: int = Query(default=50, le=100, ge=1),
    offset: int = Query(default=0, ge=0),
    action: Optional[str] = Query(default=None, description="Filter by action type"),
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type"),
    start_date: Optional[datetime] = Query(default=None, description="Filter logs from this date"),
    end_date: Optional[datetime] = Query(default=None, description="Filter logs until this date"),
):
    """
    List activity logs with role-based data isolation.

    Data Isolation Rules:
    - **Salesmen**: Can ONLY see activity logs where user_id matches their own ID
    - **Admins**: Can see ALL activity logs in the system

    The filtering is applied at the SQL query level to prevent unauthorized data exposure.

    Query Parameters:
    - limit: Maximum number of logs to return (default 50, max 100)
    - offset: Number of logs to skip for pagination
    - action: Filter by specific action type (e.g., "CREATE_ORDER")
    - entity_type: Filter by entity type (e.g., "order", "payment")
    - start_date: Only return logs from this date onwards
    - end_date: Only return logs up to this date

    Returns:
    - Paginated list of activity logs with total count
    """
    # Base query
    query = select(ActivityLog)

    # =========================================================
    # ROLE-BASED DATA ISOLATION - Applied at query level
    # This ensures data is never loaded for unauthorized users
    # =========================================================
    if current_user.role == UserRole.SALESMAN.value:
        # Salesmen can ONLY see their own activity logs
        query = query.filter(ActivityLog.user_id == current_user.id)
    # Admins see all logs - no filter applied

    # Apply additional filters (if specified)
    if action:
        query = query.filter(ActivityLog.action == action)
    if entity_type:
        query = query.filter(ActivityLog.entity_type == entity_type)
    if start_date:
        query = query.filter(ActivityLog.created_at >= start_date)
    if end_date:
        query = query.filter(ActivityLog.created_at <= end_date)

    # Get total count (before pagination)
    count_query = select(ActivityLog.id)
    if current_user.role == UserRole.SALESMAN.value:
        count_query = count_query.filter(ActivityLog.user_id == current_user.id)
    if action:
        count_query = count_query.filter(ActivityLog.action == action)
    if entity_type:
        count_query = count_query.filter(ActivityLog.entity_type == entity_type)
    if start_date:
        count_query = count_query.filter(ActivityLog.created_at >= start_date)
    if end_date:
        count_query = count_query.filter(ActivityLog.created_at <= end_date)

    count_result = await db.execute(count_query)
    total_count = len(count_result.scalars().all())

    # Apply ordering and pagination
    query = query.order_by(desc(ActivityLog.created_at))
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    return PaginatedActivityLogsResponse(
        total=total_count,
        logs=[ActivityLogResponse.model_validate(log) for log in logs]
    )


@router.get("/summary")
async def get_activity_summary(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_salesman_or_admin),
):
    """
    Get a summary of recent activity.

    Returns counts of different activity types.
    Salesmen see only their own activity counts.
    Admins see system-wide counts.
    """
    # Build base filter
    from sqlalchemy import func

    # Count by action type
    query = select(
        ActivityLog.action,
        func.count(ActivityLog.id).label("count")
    )
    if current_user.role == UserRole.SALESMAN.value:
        query = query.where(ActivityLog.user_id == current_user.id)
    query = query.group_by(ActivityLog.action)

    result = await db.execute(query)
    action_counts = result.all()

    # Count by entity type
    query = select(
        ActivityLog.entity_type,
        func.count(ActivityLog.id).label("count")
    )
    if current_user.role == UserRole.SALESMAN.value:
        query = query.where(ActivityLog.user_id == current_user.id)
    query = query.group_by(ActivityLog.entity_type)

    result = await db.execute(query)
    entity_counts = result.all()

    # Today's activity
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    query = select(func.count(ActivityLog.id)).where(ActivityLog.created_at >= today_start)
    if current_user.role == UserRole.SALESMAN.value:
        query = query.where(ActivityLog.user_id == current_user.id)

    result = await db.execute(query)
    today_count = result.scalar() or 0

    return {
        "total_today": today_count,
        "by_action": {row.action: row.count for row in action_counts},
        "by_entity_type": {row.entity_type: row.count for row in entity_counts},
        "user_role": current_user.role,
        "filtered_by_user": current_user.role == UserRole.SALESMAN.value
    }
