"""
Notifications Routes
API endpoints for notification management
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.utils.security import get_current_active_user
from app.services.enhanced_notification_service import EnhancedNotificationService

router = APIRouter()


@router.get("/")
async def get_notifications(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's notifications"""

    notifications = EnhancedNotificationService.get_user_notifications(
        db, current_user.id, page, per_page, unread_only, notification_type
    )

    return notifications


@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""

    success = EnhancedNotificationService.mark_as_read(db, notification_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return {"message": "Notification marked as read"}


@router.post("/mark-all-read")
async def mark_all_notifications_as_read(
    notification_type: Optional[str] = Body(None, description="Optional: mark only specific type as read"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""

    count = EnhancedNotificationService.mark_all_as_read(db, current_user.id, notification_type)

    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
async def dismiss_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Dismiss/delete notification"""

    success = EnhancedNotificationService.dismiss_notification(db, notification_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return {"message": "Notification dismissed"}


@router.get("/statistics")
async def get_notification_statistics(
    days: int = Query(30, ge=1, le=365, description="Number of days for statistics"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get notification statistics for the user"""

    stats = EnhancedNotificationService.get_notification_statistics(db, current_user.id, days)
    return stats


@router.post("/test")
async def create_test_notification(
    title: str = Body(..., max_length=200, description="Notification title"),
    message: str = Body(..., max_length=1000, description="Notification message"),
    notification_type: str = Body("system_maintenance", description="Notification type"),
    priority: str = Body("medium", description="Notification priority"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a test notification (for development/testing)"""

    # Admin-only access for debug endpoint
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    notification = EnhancedNotificationService.create_notification(
        db, current_user.id, notification_type, title, message, priority
    )

    return {
        "message": "Test notification created",
        "notification_id": notification.id
    }
