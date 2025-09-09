"""
Push Notification Management Routes
Device registration, notification sending, and analytics
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator

from database import get_db
from app.models.user import User
from app.services.push_notification_service import (
    PushNotificationService, DevicePlatform, push_service
)
from app.services.audit_service import AuditService
from app.utils.security import get_current_active_user, get_current_user
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class DeviceRegistration(BaseModel):
    """Device registration request"""
    token: str
    platform: str
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    app_version: Optional[str] = None
    os_version: Optional[str] = None

    @validator('platform')
    def validate_platform(cls, v):
        if v not in [DevicePlatform.IOS, DevicePlatform.ANDROID, DevicePlatform.WEB]:
            raise ValueError('Platform must be ios, android, or web')
        return v

    @validator('token')
    def validate_token(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Invalid device token')
        return v


class PushNotificationRequest(BaseModel):
    """Push notification send request (Admin only)"""
    user_ids: Optional[List[int]] = None  # Specific users, or None for all users
    title: str
    body: str
    data: Optional[dict] = None
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    platforms: Optional[List[str]] = None  # Filter by platforms

    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Title is required')
        if len(v) > 200:
            raise ValueError('Title must be 200 characters or less')
        return v.strip()

    @validator('body')
    def validate_body(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Body is required')
        if len(v) > 1000:
            raise ValueError('Body must be 1000 characters or less')
        return v.strip()


class TestNotificationRequest(BaseModel):
    """Test notification request"""
    title: str = "MyTypist Test Notification"
    body: str = "This is a test notification from MyTypist"
    data: Optional[dict] = None


@router.post("/register-device")
async def register_device_token(
    device_data: DeviceRegistration,
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Register device token for push notifications"""

    try:
        # Register the device token
        device_token = await PushNotificationService.register_device_token(
            db=db,
            user_id=current_user.id,
            token=device_data.token,
            platform=device_data.platform,
            device_id=device_data.device_id,
            device_name=device_data.device_name,
            app_version=device_data.app_version,
            os_version=device_data.os_version
        )

        # Log device registration
        AuditService.log_auth_event(
            "DEVICE_TOKEN_REGISTERED",
            current_user.id,
            request,
            {
                "platform": device_data.platform,
                "device_id": device_data.device_id,
                "device_name": device_data.device_name
            }
        )

        return {
            "success": True,
            "message": "Device token registered successfully",
            "device_id": device_token.id,
            "platform": device_token.platform
        }

    except Exception as e:
        logger.error(f"Device token registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register device token"
        )


@router.delete("/unregister-device")
async def unregister_device_token(
    token: str,
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Unregister device token"""

    try:
        success = await PushNotificationService.unregister_device_token(db, token)

        if success:
            # Log device unregistration
            AuditService.log_auth_event(
                "DEVICE_TOKEN_UNREGISTERED",
                current_user.id,
                request,
                {"token_prefix": token[:10] + "..."}
            )

            return {
                "success": True,
                "message": "Device token unregistered successfully"
            }
        else:
            return {
                "success": False,
                "message": "Device token not found or already inactive"
            }

    except Exception as e:
        logger.error(f"Device token unregistration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister device token"
        )


@router.get("/my-devices")
async def get_my_devices(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's registered devices"""

    try:
        devices = await PushNotificationService.get_user_device_tokens(current_user.id)

        # Remove sensitive token data
        safe_devices = []
        for device in devices:
            safe_devices.append({
                "id": device["id"],
                "platform": device["platform"],
                "device_id": device["device_id"],
                "device_name": device["device_name"],
                "token_prefix": device["token"][:10] + "..." if device["token"] else None
            })

        return {
            "success": True,
            "devices": safe_devices,
            "count": len(safe_devices)
        }

    except Exception as e:
        logger.error(f"Get user devices failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user devices"
        )


@router.post("/test-notification")
async def send_test_notification(
    test_data: TestNotificationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send test notification to current user's devices"""

    try:
        # Prepare notification payload
        payload = {
            "title": test_data.title,
            "body": test_data.body,
            "data": test_data.data or {
                "type": "test_notification",
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        # Send to user's devices
        results = await push_service.send_to_user_devices(
            user_id=current_user.id,
            payload=payload
        )

        successful_sends = sum(1 for result in results if result.get("success"))
        total_sends = len(results)

        return {
            "success": True,
            "message": f"Test notification sent to {successful_sends}/{total_sends} devices",
            "devices_reached": successful_sends,
            "total_devices": total_sends,
            "results": results
        }

    except Exception as e:
        logger.error(f"Test notification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notification"
        )


@router.post("/admin/send-notification")
async def send_push_notification(
    notification_data: PushNotificationRequest,
    current_user: User = Depends(get_current_active_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Send push notification to users (Admin only)"""

    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    try:
        # Prepare notification payload
        payload = {
            "title": notification_data.title,
            "body": notification_data.body,
            "data": notification_data.data or {}
        }

        if notification_data.action_url:
            payload["data"]["action_url"] = notification_data.action_url
        if notification_data.action_text:
            payload["data"]["action_text"] = notification_data.action_text

        # Determine target users
        if notification_data.user_ids:
            target_users = db.query(User).filter(User.id.in_(notification_data.user_ids)).all()
        else:
            # Send to all active users (be careful with this!)
            target_users = db.query(User).filter(User.status == "active").all()

        if not target_users:
            return {
                "success": False,
                "message": "No target users found"
            }

        # Send notifications
        total_results = []
        successful_users = 0

        for user in target_users:
            try:
                # Get user's device tokens
                device_tokens = await PushNotificationService.get_user_device_tokens(user.id)

                # Filter by platforms if specified
                if notification_data.platforms:
                    device_tokens = [
                        device for device in device_tokens
                        if device["platform"] in notification_data.platforms
                    ]

                if device_tokens:
                    user_results = await push_service.send_to_user_devices(
                        user_id=user.id,
                        payload=payload,
                        device_tokens=device_tokens
                    )
                    total_results.extend(user_results)

                    if any(result.get("success") for result in user_results):
                        successful_users += 1

            except Exception as e:
                logger.error(f"Failed to send notification to user {user.id}: {e}")
                continue

        # Log admin notification send
        AuditService.log_auth_event(
            "ADMIN_PUSH_NOTIFICATION_SENT",
            current_user.id,
            request,
            {
                "target_users": len(target_users),
                "successful_users": successful_users,
                "title": notification_data.title,
                "platforms": notification_data.platforms
            }
        )

        successful_sends = sum(1 for result in total_results if result.get("success"))
        total_sends = len(total_results)

        return {
            "success": True,
            "message": f"Notification sent to {successful_users}/{len(target_users)} users",
            "target_users": len(target_users),
            "successful_users": successful_users,
            "devices_reached": successful_sends,
            "total_devices": total_sends,
            "summary": {
                "user_success_rate": (successful_users / len(target_users) * 100) if target_users else 0,
                "device_success_rate": (successful_sends / total_sends * 100) if total_sends > 0 else 0
            }
        }

    except Exception as e:
        logger.error(f"Admin push notification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send push notification"
        )


@router.get("/admin/statistics")
async def get_push_statistics(
    days: int = 30,
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get push notification statistics (Admin only)"""

    # Check admin permissions
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    try:
        stats = await PushNotificationService.get_push_statistics(user_id, days)

        return {
            "success": True,
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Get push statistics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve push statistics"
        )


@router.get("/my-statistics")
async def get_my_push_statistics(
    days: int = 30,
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's push notification statistics"""

    try:
        stats = await PushNotificationService.get_push_statistics(current_user.id, days)

        return {
            "success": True,
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Get user push statistics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve push statistics"
        )
