"""Notification service for handling user notifications"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean, Text, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import Base
import logging

logger = logging.getLogger(__name__)


class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    type = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), nullable=False, default="normal")
    read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=True)


class NotificationService:
    """Service for managing user notifications"""

    PRIORITY_LEVELS = ["low", "normal", "high", "urgent"]
    DEFAULT_EXPIRE_DAYS = 30

    @staticmethod
    async def send_notification(
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        notification_type: str = "general",
        priority: str = "normal",
        expire_days: int = DEFAULT_EXPIRE_DAYS
    ) -> bool:
        """Send a notification to a user"""
        try:
            async with AsyncSession() as db:
                # Validate priority
                if priority not in NotificationService.PRIORITY_LEVELS:
                    priority = "normal"

                # Create notification
                notification = Notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    data=data,
                    type=notification_type,
                    priority=priority,
                    expires_at=datetime.utcnow().date() + timedelta(days=expire_days) if expire_days else None
                )
                
                db.add(notification)
                await db.commit()
                await db.refresh(notification)

                # Send push notification if applicable
                await NotificationService._send_push_notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    data=data,
                    priority=priority
                )

                return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    @staticmethod
    async def get_user_notifications(
        user_id: int,
        unread_only: bool = False,
        notification_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get notifications for a user"""
        try:
            async with AsyncSession() as db:
                query = db.query(Notification).filter(
                    Notification.user_id == user_id
                )

                if unread_only:
                    query = query.filter(Notification.read == False)
                
                if notification_type:
                    query = query.filter(Notification.type == notification_type)

                total = await query.count()
                
                notifications = await query.order_by(Notification.created_at.desc())\
                    .offset(offset)\
                    .limit(limit)\
                    .all()

                return {
                    "success": True,
                    "total": total,
                    "notifications": [
                        {
                            "id": n.id,
                            "title": n.title,
                            "body": n.body,
                            "data": n.data,
                            "type": n.type,
                            "priority": n.priority,
                            "read": n.read,
                            "created_at": n.created_at.isoformat()
                        } for n in notifications
                    ]
                }

        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            return {
                "success": False,
                "message": "Failed to retrieve notifications"
            }

    @staticmethod
    async def mark_as_read(
        user_id: int,
        notification_ids: List[int]
    ) -> Dict[str, Any]:
        """Mark notifications as read"""
        try:
            async with AsyncSession() as db:
                result = await db.query(Notification).filter(
                    Notification.user_id == user_id,
                    Notification.id.in_(notification_ids),
                    Notification.read == False
                ).update({
                    Notification.read: True,
                    Notification.read_at: datetime.utcnow()
                })

                await db.commit()

                return {
                    "success": True,
                    "marked_read": result
                }

        except Exception as e:
            logger.error(f"Failed to mark notifications as read: {e}")
            return {
                "success": False,
                "message": "Failed to mark notifications as read"
            }

    @staticmethod
    async def delete_notifications(
        user_id: int,
        notification_ids: List[int]
    ) -> Dict[str, Any]:
        """Delete notifications for a user"""
        try:
            async with AsyncSession() as db:
                result = await db.query(Notification).filter(
                    Notification.user_id == user_id,
                    Notification.id.in_(notification_ids)
                ).delete()

                await db.commit()

                return {
                    "success": True,
                    "deleted": result
                }

        except Exception as e:
            logger.error(f"Failed to delete notifications: {e}")
            return {
                "success": False,
                "message": "Failed to delete notifications"
            }

    @staticmethod
    async def _send_push_notification(
        user_id: int,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal"
    ) -> bool:
        """Send push notification if user has enabled them"""
        try:
            # Get user's push notification settings and tokens
            user_settings = await NotificationService._get_user_notification_settings(user_id)
            
            if not user_settings.get("push_enabled", False):
                return False

            # Send to appropriate push service (FCM, APNS, etc.)
            push_service = NotificationService._get_push_service(user_settings.get("platform"))
            if push_service:
                await push_service.send(
                    token=user_settings.get("push_token"),
                    title=title,
                    body=body,
                    data=data,
                    priority=priority
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False

    @staticmethod
    async def _get_user_notification_settings(user_id: int) -> Dict[str, Any]:
        """Get user's notification settings"""
        try:
            async with AsyncSession() as db:
                # Implementation: Get user settings from database
                return {
                    "push_enabled": True,  # Placeholder
                    "platform": "fcm",  # Placeholder
                    "push_token": None  # Placeholder
                }
        except Exception:
            return {
                "push_enabled": False
            }

    @staticmethod
    def _get_push_service(platform: str):
        """Get appropriate push notification service"""
        # Implementation: Return appropriate push service based on platform
        return None  # Placeholder