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
from app.services.notification_service import NotificationService

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

    notifications = await NotificationService.get_user_notifications(
        current_user.id, unread_only=unread_only, notification_type=notification_type,
        limit=per_page, offset=(page-1)*per_page
    )

    return notifications


@router.post("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""

    success = await NotificationService.mark_as_read(current_user.id, [notification_id])

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

    result = await NotificationService.mark_as_read(current_user.id, [])
    # NotificationService.mark_as_read returns dict; adapt response
    count = result.get("marked_read", 0) if isinstance(result, dict) else 0

    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
async def dismiss_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Dismiss/delete notification"""

    # NotificationService currently does not expose dismiss; delete via delete_notifications
    result = await NotificationService.delete_notifications(current_user.id, [notification_id])
    success = result.get("deleted", 0) > 0 if isinstance(result, dict) else False

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

    # Notification statistics endpoint not implemented in lightweight NotificationService
    return {"message": "Statistics endpoint not available in simplified NotificationService"}


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

    # Create a notification using the simplified NotificationService
    success = await NotificationService.send_notification(
        current_user.id, title, message, data=None, notification_type=notification_type, priority=priority
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to create notification")

    return {"message": "Test notification created"}

    return {
        "message": "Test notification created",
        "notification_id": notification.id
    }
