"""
Enhanced Notification Service
Comprehensive notification system for security alerts, user activities, and system events
"""
import logging

logger = logging.getLogger(__name__)
class NotificationPreferences(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)

    # Channel preferences
    email_enabled = Column(Boolean, nullable=False, default=True)
    in_app_enabled = Column(Boolean, nullable=False, default=True)
    sms_enabled = Column(Boolean, nullable=False, default=False)
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, func, desc, and_
from sqlalchemy.orm import relationship
from enum import Enum
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
from jinja2 import Template as JinjaTemplate

from database import Base
from app.models.user import User
from config import settings
from app.services.email_service import EmailService


class NotificationType(str, Enum):
    """Notification types"""
    SECURITY_ALERT = "security_alert"
    DOCUMENT_READY = "document_ready"
    DOCUMENT_SHARED = "document_shared"
    TEMPLATE_PURCHASED = "template_purchased"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    ACCOUNT_UPDATE = "account_update"
    SYSTEM_MAINTENANCE = "system_maintenance"
    SUBSCRIPTION_EXPIRY = "subscription_expiry"
    LOGIN_ANOMALY = "login_anomaly"
    PASSWORD_CHANGED = "password_changed"
    TWO_FACTOR_ENABLED = "two_factor_enabled"
    API_KEY_CREATED = "api_key_created"
    WALLET_TRANSACTION = "wallet_transaction"
    TEMPLATE_APPROVED = "template_approved"
    TEMPLATE_REJECTED = "template_rejected"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"


class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # Notification details
    type = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), nullable=False, default=NotificationPriority.MEDIUM, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Rich content
    notification_metadata = Column(JSON, nullable=True)  # Additional data
    action_url = Column(String(500), nullable=True)  # URL for action button
    action_text = Column(String(100), nullable=True)  # Action button text

    # Delivery
    channels = Column(JSON, nullable=False, default=list)  # List of channels to send to
    sent_channels = Column(JSON, nullable=False, default=list)  # Successfully sent channels
    failed_channels = Column(JSON, nullable=False, default=list)  # Failed channels

    # Status
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    read_at = Column(DateTime, nullable=True)
    is_dismissed = Column(Boolean, nullable=False, default=False)
    dismissed_at = Column(DateTime, nullable=True)

    # Delivery attempts
    delivery_attempts = Column(Integer, nullable=False, default=0)
    last_delivery_attempt = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)

    # Expiration
    expires_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="notifications")


class NotificationTemplate(Base):
    """Notification templates"""
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False, unique=True, index=True)

    # Template content
    title_template = Column(String(200), nullable=False)
    message_template = Column(Text, nullable=False)
    email_subject_template = Column(String(200), nullable=True)
    email_body_template = Column(Text, nullable=True)

    # Settings
    default_channels = Column(JSON, nullable=False, default=list)
    default_priority = Column(String(20), nullable=False, default=NotificationPriority.MEDIUM)
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class NotificationPreference(Base):
    """User notification preferences"""
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True, index=True)

    # Channel preferences
    email_enabled = Column(Boolean, nullable=False, default=True)
    sms_enabled = Column(Boolean, nullable=False, default=False)
    push_enabled = Column(Boolean, nullable=False, default=True)
    in_app_enabled = Column(Boolean, nullable=False, default=True)

    # Type preferences (JSON with type -> enabled mapping)
    type_preferences = Column(JSON, nullable=False, default=dict)

    # Quiet hours
    quiet_hours_enabled = Column(Boolean, nullable=False, default=False)
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=True)    # HH:MM format

    # Frequency limits
    max_emails_per_day = Column(Integer, nullable=False, default=10)
    max_sms_per_day = Column(Integer, nullable=False, default=3)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="notification_preferences")


class EnhancedNotificationService:
    """Enhanced notification service"""

    def __init__(self):
        self.email_service = EmailService()

    @staticmethod
    def create_notification(db: Session, user_id: int, notification_type: str,
                           title: str, message: str, priority: str = NotificationPriority.MEDIUM,
                           channels: List[str] = None, metadata: Dict = None,
                           action_url: str = None, action_text: str = None,
                           expires_at: datetime = None) -> Notification:
        """Create a new notification"""

        if channels is None:
            # Get default channels from template or user preferences
            channels = EnhancedNotificationService._get_default_channels(db, user_id, notification_type)

        notification = Notification(
            user_id=user_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            channels=channels,
            metadata=metadata or {},
            action_url=action_url,
            action_text=action_text,
            expires_at=expires_at
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        # Trigger immediate delivery for high priority notifications
        if priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL]:
            asyncio.create_task(
                EnhancedNotificationService._deliver_notification_async(db, notification.id)
            )

        return notification

    @staticmethod
    def create_from_template(db: Session, user_id: int, notification_type: str,
                           template_data: Dict = None) -> Optional[Notification]:
        """Create notification from template"""

        template = db.query(NotificationTemplate).filter(
            NotificationTemplate.type == notification_type,
            NotificationTemplate.is_active == True
        ).first()

        if not template:
            return None

        template_data = template_data or {}

        # Render templates
        title = JinjaTemplate(template.title_template).render(**template_data)
        message = JinjaTemplate(template.message_template).render(**template_data)

        return EnhancedNotificationService.create_notification(
            db, user_id, notification_type, title, message,
            priority=template.default_priority,
            channels=template.default_channels,
            metadata=template_data
        )

    @staticmethod
    def get_user_notifications(db: Session, user_id: int, page: int = 1, per_page: int = 20,
                              unread_only: bool = False, notification_type: str = None) -> Dict:
        """Get user's notifications"""

        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_dismissed == False
        )

        if unread_only:
            query = query.filter(Notification.is_read == False)

        if notification_type:
            query = query.filter(Notification.type == notification_type)

        # Check expiration
        query = query.filter(
            or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > datetime.utcnow()
            )
        )

        query = query.order_by(desc(Notification.created_at))

        total = query.count()
        notifications = query.offset((page - 1) * per_page).limit(per_page).all()

        return {
            "notifications": [
                EnhancedNotificationService._format_notification(n) for n in notifications
            ],
            "total": total,
            "unread_count": db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
                Notification.is_dismissed == False
            ).count(),
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""

        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.commit()
            return True

        return False

    @staticmethod
    def mark_all_as_read(db: Session, user_id: int, notification_type: str = None) -> int:
        """Mark all notifications as read"""

        query = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        )

        if notification_type:
            query = query.filter(Notification.type == notification_type)

        count = query.count()
        query.update({
            "is_read": True,
            "read_at": datetime.utcnow()
        })
        db.commit()

        return count

    @staticmethod
    def dismiss_notification(db: Session, notification_id: int, user_id: int) -> bool:
        """Dismiss notification"""

        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()

        if notification:
            notification.is_dismissed = True
            notification.dismissed_at = datetime.utcnow()
            db.commit()
            return True

        return False

    @staticmethod
    async def deliver_notification(db: Session, notification_id: int) -> Dict:
        """Deliver notification through configured channels"""

        notification = db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

        if not notification:
            return {"success": False, "error": "Notification not found"}

        user = notification.user
        if not user:
            return {"success": False, "error": "User not found"}

        # Check user preferences
        preferences = EnhancedNotificationService._get_user_preferences(db, user.id)

        # Check quiet hours
        if EnhancedNotificationService._is_quiet_hours(preferences):
            # Schedule for later delivery
            notification.next_retry_at = EnhancedNotificationService._get_next_delivery_time(preferences)
            db.commit()
            return {"success": True, "message": "Scheduled for delivery after quiet hours"}

        delivery_results = {}

        for channel in notification.channels:
            try:
                if channel == NotificationChannel.EMAIL and preferences.email_enabled:
                    result = await EnhancedNotificationService._send_email(notification, user)
                    delivery_results[channel] = result

                elif channel == NotificationChannel.IN_APP and preferences.in_app_enabled:
                    # In-app notifications are already stored in database
                    delivery_results[channel] = {"success": True}

                elif channel == NotificationChannel.SMS and preferences.sms_enabled:
                    result = await EnhancedNotificationService._send_sms(notification, user)
                    delivery_results[channel] = result

            except Exception as e:
                delivery_results[channel] = {"success": False, "error": str(e)}

        # Update notification delivery status
        successful_channels = [ch for ch, result in delivery_results.items() if result.get("success")]
        failed_channels = [ch for ch, result in delivery_results.items() if not result.get("success")]

        notification.sent_channels = list(set(notification.sent_channels + successful_channels))
        notification.failed_channels = list(set(notification.failed_channels + failed_channels))
        notification.delivery_attempts += 1
        notification.last_delivery_attempt = datetime.utcnow()

        # Schedule retry for failed channels if needed
        if failed_channels and notification.delivery_attempts < 3:
            notification.next_retry_at = datetime.utcnow() + timedelta(minutes=15 * notification.delivery_attempts)

        db.commit()

        return {
            "success": len(successful_channels) > 0,
            "delivered_channels": successful_channels,
            "failed_channels": failed_channels,
            "results": delivery_results
        }

    @staticmethod
    def create_security_alert(db: Session, user_id: int, alert_type: str,
                             details: Dict, ip_address: str = None) -> Notification:
        """Create security alert notification"""

        alert_messages = {
            "login_anomaly": "Unusual login activity detected on your account",
            "password_changed": "Your account password has been changed",
            "two_factor_disabled": "Two-factor authentication has been disabled",
            "api_key_created": "A new API key has been created for your account",
            "suspicious_activity": "Suspicious activity detected on your account"
        }

        title = "Security Alert"
        message = alert_messages.get(alert_type, "Security event detected on your account")

        metadata = {
            "alert_type": alert_type,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
            **details
        }

        return EnhancedNotificationService.create_notification(
            db, user_id, NotificationType.SECURITY_ALERT,
            title, message, NotificationPriority.HIGH,
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            metadata=metadata
        )

    @staticmethod
    def create_document_notification(db: Session, user_id: int, document_id: int,
                                   event_type: str, document_title: str) -> Notification:
        """Create document-related notification"""

        messages = {
            "ready": f"Your document '{document_title}' is ready for download",
            "shared": f"Document '{document_title}' has been shared with you",
            "signed": f"Document '{document_title}' has been signed",
            "expired": f"Document '{document_title}' has expired"
        }

        return EnhancedNotificationService.create_notification(
            db, user_id, NotificationType.DOCUMENT_READY,
            "Document Update", messages.get(event_type, "Document status updated"),
            metadata={"document_id": document_id, "event_type": event_type},
            action_url=f"/documents/{document_id}",
            action_text="View Document"
        )

    @staticmethod
    def create_payment_notification(db: Session, user_id: int, payment_id: int,
                                  amount: float, status: str, description: str) -> Notification:
        """Create payment-related notification"""

        if status == "completed":
            title = "Payment Successful"
            message = f"Your payment of ₦{amount:,.2f} for {description} was successful"
            priority = NotificationPriority.MEDIUM
        else:
            title = "Payment Failed"
            message = f"Your payment of ₦{amount:,.2f} for {description} failed. Please try again."
            priority = NotificationPriority.HIGH

        return EnhancedNotificationService.create_notification(
            db, user_id, NotificationType.PAYMENT_SUCCESS if status == "completed" else NotificationType.PAYMENT_FAILED,
            title, message, priority,
            metadata={"payment_id": payment_id, "amount": amount, "status": status}
        )

    @staticmethod
    async def _deliver_notification_async(db: Session, notification_id: int):
        """Async wrapper for notification delivery"""
        await EnhancedNotificationService.deliver_notification(db, notification_id)

    @staticmethod
    async def _send_email(notification: Notification, user: User) -> Dict:
        """Send email notification"""

        try:
            # Get email template
            template = db.query(NotificationTemplate).filter(
                NotificationTemplate.type == notification.type
            ).first()

            if template and template.email_subject_template and template.email_body_template:
                subject = JinjaTemplate(template.email_subject_template).render(
                    user=user, notification=notification, **notification.metadata
                )
                body = JinjaTemplate(template.email_body_template).render(
                    user=user, notification=notification, **notification.metadata
                )
            else:
                subject = notification.title
                body = notification.message

            # Send email using real EmailService with error handling
            try:
                from app.services.email_service import email_service

                result = await email_service.send_email(
                    to_email=user.email,
                    subject=subject,
                    template_name="notification",
                    template_data={
                        'user_name': user.full_name or user.email,
                        'title': notification.title,
                        'message': body,
                        'action_url': notification.action_url,
                        'action_text': notification.action_text,
                        'metadata': notification.metadata or {}
                    }
                )

                return result

            except ImportError:
                # Fallback if email service is not available
                logger.warning("EmailService not available, notification email not sent")
                return {"success": False, "error": "Email service not configured"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def _send_sms(notification: Notification, user: User) -> Dict:
        """Send SMS notification"""
        # SMS is not needed per user requirements
        return {"success": False, "error": "SMS service not configured (not required)"}

    @staticmethod
    async def _send_push(notification: Notification, user: User) -> Dict:
        """Send push notification via Firebase Cloud Messaging and Apple Push Notifications"""
        try:
            # Import push notification services
            from app.services.push_notification_service import PushNotificationService

            # Get user's device tokens
            device_tokens = await PushNotificationService.get_user_device_tokens(user.id)

            if not device_tokens:
                return {"success": False, "error": "No device tokens found for user"}

            # Prepare push notification payload
            push_payload = {
                "title": notification.title,
                "body": notification.message,
                "data": {
                    "notification_id": str(notification.id),
                    "type": notification.type,
                    "priority": notification.priority,
                    "action_url": notification.action_url,
                    "metadata": notification.metadata
                }
            }

            # Add action button if specified
            if notification.action_url and notification.action_text:
                push_payload["data"]["action_text"] = notification.action_text

            # Send to all user devices
            results = await PushNotificationService.send_to_user_devices(
                user_id=user.id,
                payload=push_payload,
                device_tokens=device_tokens
            )

            # Check results
            successful_sends = sum(1 for result in results if result.get("success"))
            total_sends = len(results)

            if successful_sends > 0:
                return {
                    "success": True,
                    "devices_reached": successful_sends,
                    "total_devices": total_sends,
                    "results": results
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to send to all {total_sends} devices",
                    "results": results
                }

        except ImportError:
            return {"success": False, "error": "Push notification service not available"}
        except Exception as e:
            return {"success": False, "error": f"Push notification failed: {str(e)}"}

    @staticmethod
    def _get_user_preferences(db: Session, user_id: int) -> NotificationPreference:
        """Get user's notification preferences"""

        preferences = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id
        ).first()

        if not preferences:
            # Create default preferences
            preferences = NotificationPreference(user_id=user_id)
            db.add(preferences)
            db.commit()

        return preferences

    @staticmethod
    def _get_default_channels(db: Session, user_id: int, notification_type: str) -> List[str]:
        """Get default channels for notification type"""

        # Check template defaults
        template = db.query(NotificationTemplate).filter(
            NotificationTemplate.type == notification_type
        ).first()

        if template:
            return template.default_channels

        # Fallback to user preferences
        preferences = EnhancedNotificationService._get_user_preferences(db, user_id)
        channels = [NotificationChannel.IN_APP]  # Always include in-app

        if preferences.email_enabled:
            channels.append(NotificationChannel.EMAIL)

        return channels

    @staticmethod
    def _is_quiet_hours(preferences: NotificationPreference) -> bool:
        """Check if current time is within user's quiet hours"""

        if not preferences.quiet_hours_enabled or not preferences.quiet_hours_start or not preferences.quiet_hours_end:
            return False

        now = datetime.utcnow().time()
        start_time = datetime.strptime(preferences.quiet_hours_start, "%H:%M").time()
        end_time = datetime.strptime(preferences.quiet_hours_end, "%H:%M").time()

        if start_time <= end_time:
            return start_time <= now <= end_time
        else:  # Quiet hours span midnight
            return now >= start_time or now <= end_time

    @staticmethod
    def _get_next_delivery_time(preferences: NotificationPreference) -> datetime:
        """Get next delivery time after quiet hours"""

        if not preferences.quiet_hours_end:
            return datetime.utcnow() + timedelta(hours=1)

        end_time = datetime.strptime(preferences.quiet_hours_end, "%H:%M").time()
        next_delivery = datetime.combine(datetime.utcnow().date(), end_time)

        if next_delivery <= datetime.utcnow():
            next_delivery += timedelta(days=1)

        return next_delivery

    @staticmethod
    def _format_notification(notification: Notification) -> Dict:
        """Format notification for API response"""

        return {
            "id": notification.id,
            "type": notification.type,
            "priority": notification.priority,
            "title": notification.title,
            "message": notification.message,
            "metadata": notification.metadata,
            "action_url": notification.action_url,
            "action_text": notification.action_text,
            "is_read": notification.is_read,
            "read_at": notification.read_at,
            "created_at": notification.created_at,
            "expires_at": notification.expires_at,
            "delivery_status": {
                "sent_channels": notification.sent_channels,
                "failed_channels": notification.failed_channels,
                "attempts": notification.delivery_attempts
            }
        }

    @staticmethod
    def get_notification_statistics(db: Session, user_id: Optional[int] = None, days: int = 30) -> Dict:
        """Get notification statistics"""

        start_date = datetime.utcnow() - timedelta(days=days)

        query = db.query(Notification).filter(Notification.created_at >= start_date)

        if user_id:
            query = query.filter(Notification.user_id == user_id)

        notifications = query.all()

        # Calculate statistics
        total_notifications = len(notifications)
        read_notifications = len([n for n in notifications if n.is_read])
        unread_notifications = total_notifications - read_notifications

        # Group by type
        type_counts = {}
        for notification in notifications:
            type_counts[notification.type] = type_counts.get(notification.type, 0) + 1

        # Group by priority
        priority_counts = {}
        for notification in notifications:
            priority_counts[notification.priority] = priority_counts.get(notification.priority, 0) + 1

        return {
            "period_days": days,
            "total_notifications": total_notifications,
            "read_notifications": read_notifications,
            "unread_notifications": unread_notifications,
            "read_percentage": (read_notifications / total_notifications * 100) if total_notifications > 0 else 0,
            "type_breakdown": type_counts,
            "priority_breakdown": priority_counts,
            "delivery_success_rate": EnhancedNotificationService._calculate_delivery_success_rate(notifications)
        }

    @staticmethod
    def _calculate_delivery_success_rate(notifications: List[Notification]) -> float:
        """Calculate delivery success rate"""

        total_attempts = sum(len(n.channels) for n in notifications)
        successful_deliveries = sum(len(n.sent_channels) for n in notifications)

        if total_attempts == 0:
            return 100.0

        return (successful_deliveries / total_attempts) * 100
