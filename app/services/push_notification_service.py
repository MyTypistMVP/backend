"""
Production-ready Push Notification Service
Firebase Cloud Messaging (FCM) and Apple Push Notification Service (APNS) integration
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from enum import Enum
import httpx
import jwt
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from database import Base, get_db
from config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


class DevicePlatform(str, Enum):
    """Device platform types"""
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class DeviceToken(Base):
    """User device tokens for push notifications"""
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # Device information
    token = Column(String(500), nullable=False, index=True, unique=True)
    platform = Column(String(20), nullable=False, index=True)
    device_id = Column(String(200), nullable=True)
    device_name = Column(String(200), nullable=True)
    app_version = Column(String(50), nullable=True)
    os_version = Column(String(50), nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    last_used = Column(DateTime, nullable=True)

    # Failure tracking
    failure_count = Column(Integer, nullable=False, default=0)
    last_failure = Column(DateTime, nullable=True)
    failure_reason = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="device_tokens")


class PushNotificationLog(Base):
    """Push notification delivery log"""
    __tablename__ = "push_notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    device_token_id = Column(Integer, ForeignKey('device_tokens.id'), nullable=True, index=True)

    # Notification details
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)

    # Delivery
    platform = Column(String(20), nullable=False)
    status = Column(String(50), nullable=False, index=True)  # sent, delivered, failed, clicked
    response_data = Column(JSON, nullable=True)
    error_message = Column(String(1000), nullable=True)

    # Metrics
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    delivered_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="push_logs")
    device_token = relationship("DeviceToken", backref="push_logs")


class FirebaseCloudMessaging:
    """Firebase Cloud Messaging service"""

    def __init__(self):
        self.server_key = settings.FCM_SERVER_KEY if hasattr(settings, 'FCM_SERVER_KEY') else None
        self.project_id = settings.FCM_PROJECT_ID if hasattr(settings, 'FCM_PROJECT_ID') else None
        self.service_account_key = settings.FCM_SERVICE_ACCOUNT_KEY if hasattr(settings, 'FCM_SERVICE_ACCOUNT_KEY') else None

        if not self.server_key and not self.service_account_key:
            logger.warning("FCM credentials not configured")

    async def send_notification(self, token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification via FCM"""
        try:
            if not self.server_key:
                return {"success": False, "error": "FCM server key not configured"}

            # Prepare FCM payload
            fcm_payload = {
                "to": token,
                "notification": {
                    "title": payload.get("title", ""),
                    "body": payload.get("body", ""),
                    "icon": "ic_notification",
                    "sound": "default",
                    "click_action": payload.get("data", {}).get("action_url", "")
                },
                "data": payload.get("data", {}),
                "priority": "high",
                "time_to_live": 3600  # 1 hour
            }

            # Add Android-specific configuration
            fcm_payload["android"] = {
                "priority": "high",
                "notification": {
                    "icon": "ic_notification",
                    "color": "#1976D2",  # MyTypist brand color
                    "sound": "default",
                    "click_action": payload.get("data", {}).get("action_url", "")
                }
            }

            # Send request to FCM
            headers = {
                "Authorization": f"key={self.server_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://fcm.googleapis.com/fcm/send",
                    json=fcm_payload,
                    headers=headers,
                    timeout=30
                )

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success", 0) > 0:
                    return {
                        "success": True,
                        "message_id": response_data.get("results", [{}])[0].get("message_id"),
                        "response": response_data
                    }
                else:
                    error = response_data.get("results", [{}])[0].get("error", "Unknown error")
                    return {"success": False, "error": error, "response": response_data}
            else:
                return {
                    "success": False,
                    "error": f"FCM request failed: {response.status_code}",
                    "response": response.text
                }

        except Exception as e:
            logger.error(f"FCM send failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_to_multiple(self, tokens: List[str], payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Send notification to multiple tokens"""
        if not tokens:
            return []

        # FCM supports up to 1000 tokens per request
        batch_size = 1000
        results = []

        for i in range(0, len(tokens), batch_size):
            batch_tokens = tokens[i:i + batch_size]

            try:
                if not self.server_key:
                    results.extend([{"success": False, "error": "FCM server key not configured"} for _ in batch_tokens])
                    continue

                # Prepare multicast payload
                fcm_payload = {
                    "registration_ids": batch_tokens,
                    "notification": {
                        "title": payload.get("title", ""),
                        "body": payload.get("body", ""),
                        "icon": "ic_notification",
                        "sound": "default"
                    },
                    "data": payload.get("data", {}),
                    "priority": "high",
                    "time_to_live": 3600
                }

                headers = {
                    "Authorization": f"key={self.server_key}",
                    "Content-Type": "application/json"
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://fcm.googleapis.com/fcm/send",
                        json=fcm_payload,
                        headers=headers,
                        timeout=30
                    )

                if response.status_code == 200:
                    response_data = response.json()
                    batch_results = []

                    for idx, result in enumerate(response_data.get("results", [])):
                        if "message_id" in result:
                            batch_results.append({
                                "success": True,
                                "token": batch_tokens[idx],
                                "message_id": result["message_id"]
                            })
                        else:
                            batch_results.append({
                                "success": False,
                                "token": batch_tokens[idx],
                                "error": result.get("error", "Unknown error")
                            })

                    results.extend(batch_results)
                else:
                    error_msg = f"FCM batch request failed: {response.status_code}"
                    results.extend([{"success": False, "token": token, "error": error_msg} for token in batch_tokens])

            except Exception as e:
                logger.error(f"FCM batch send failed: {e}")
                results.extend([{"success": False, "token": token, "error": str(e)} for token in batch_tokens])

        return results


class ApplePushNotificationService:
    """Apple Push Notification Service (APNS)"""

    def __init__(self):
        self.team_id = settings.APNS_TEAM_ID if hasattr(settings, 'APNS_TEAM_ID') else None
        self.key_id = settings.APNS_KEY_ID if hasattr(settings, 'APNS_KEY_ID') else None
        self.private_key = settings.APNS_PRIVATE_KEY if hasattr(settings, 'APNS_PRIVATE_KEY') else None
        self.bundle_id = settings.APNS_BUNDLE_ID if hasattr(settings, 'APNS_BUNDLE_ID') else None
        self.is_production = settings.APNS_PRODUCTION if hasattr(settings, 'APNS_PRODUCTION') else False

        if not all([self.team_id, self.key_id, self.private_key, self.bundle_id]):
            logger.warning("APNS credentials not fully configured")

    def _generate_jwt_token(self) -> Optional[str]:
        """Generate JWT token for APNS authentication"""
        try:
            if not all([self.team_id, self.key_id, self.private_key]):
                return None

            # Load private key
            private_key = serialization.load_pem_private_key(
                self.private_key.encode(),
                password=None
            )

            # Create JWT payload
            payload = {
                "iss": self.team_id,
                "iat": int(time.time())
            }

            # Create JWT token
            token = jwt.encode(
                payload,
                private_key,
                algorithm="ES256",
                headers={"kid": self.key_id}
            )

            return token

        except Exception as e:
            logger.error(f"APNS JWT generation failed: {e}")
            return None

    async def send_notification(self, device_token: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification via APNS"""
        try:
            if not all([self.team_id, self.key_id, self.private_key, self.bundle_id]):
                return {"success": False, "error": "APNS credentials not configured"}

            # Generate JWT token
            jwt_token = self._generate_jwt_token()
            if not jwt_token:
                return {"success": False, "error": "Failed to generate APNS JWT token"}

            # Prepare APNS payload
            apns_payload = {
                "aps": {
                    "alert": {
                        "title": payload.get("title", ""),
                        "body": payload.get("body", "")
                    },
                    "sound": "default",
                    "badge": 1,
                    "content-available": 1
                }
            }

            # Add custom data
            if payload.get("data"):
                apns_payload.update(payload["data"])

            # Add action URL if available
            if payload.get("data", {}).get("action_url"):
                apns_payload["aps"]["category"] = "ACTION_CATEGORY"

            # Determine APNS server URL
            server_url = "https://api.push.apple.com" if self.is_production else "https://api.sandbox.push.apple.com"

            headers = {
                "authorization": f"bearer {jwt_token}",
                "apns-topic": self.bundle_id,
                "apns-push-type": "alert",
                "apns-priority": "10",
                "apns-expiration": str(int(time.time()) + 3600)  # 1 hour
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{server_url}/3/device/{device_token}",
                    json=apns_payload,
                    headers=headers,
                    timeout=30
                )

            if response.status_code == 200:
                return {
                    "success": True,
                    "apns_id": response.headers.get("apns-id"),
                    "status_code": response.status_code
                }
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass

                return {
                    "success": False,
                    "error": error_data.get("reason", f"APNS request failed: {response.status_code}"),
                    "status_code": response.status_code,
                    "response": error_data
                }

        except Exception as e:
            logger.error(f"APNS send failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_to_multiple(self, tokens: List[str], payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Send notification to multiple APNS tokens"""
        if not tokens:
            return []

        # APNS requires individual requests for each token
        tasks = []
        for token in tokens:
            task = self.send_notification(token, payload)
            tasks.append(task)

        # Execute requests concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "token": tokens[idx],
                    "error": str(result)
                })
            else:
                result["token"] = tokens[idx]
                processed_results.append(result)

        return processed_results


class PushNotificationService:
    """Main push notification service"""

    def __init__(self):
        self.fcm = FirebaseCloudMessaging()
        self.apns = ApplePushNotificationService()

    @staticmethod
    async def register_device_token(
        db: Session,
        user_id: int,
        token: str,
        platform: str,
        device_id: str = None,
        device_name: str = None,
        app_version: str = None,
        os_version: str = None
    ) -> DeviceToken:
        """Register or update device token"""

        # Check if token already exists
        existing_token = db.query(DeviceToken).filter(
            DeviceToken.token == token
        ).first()

        if existing_token:
            # Update existing token
            existing_token.user_id = user_id
            existing_token.platform = platform
            existing_token.device_id = device_id or existing_token.device_id
            existing_token.device_name = device_name or existing_token.device_name
            existing_token.app_version = app_version or existing_token.app_version
            existing_token.os_version = os_version or existing_token.os_version
            existing_token.is_active = True
            existing_token.last_used = datetime.utcnow()
            existing_token.failure_count = 0  # Reset failure count
            existing_token.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(existing_token)
            return existing_token

        # Create new token
        device_token = DeviceToken(
            user_id=user_id,
            token=token,
            platform=platform,
            device_id=device_id,
            device_name=device_name,
            app_version=app_version,
            os_version=os_version,
            last_used=datetime.utcnow()
        )

        db.add(device_token)
        db.commit()
        db.refresh(device_token)

        logger.info(f"Registered new device token for user {user_id}, platform {platform}")
        return device_token

    @staticmethod
    async def get_user_device_tokens(user_id: int) -> List[Dict[str, Any]]:
        """Get all active device tokens for a user"""
        db = next(get_db())
        try:
            tokens = db.query(DeviceToken).filter(
                DeviceToken.user_id == user_id,
                DeviceToken.is_active == True,
                DeviceToken.failure_count < 5  # Exclude tokens with too many failures
            ).all()

            return [
                {
                    "id": token.id,
                    "token": token.token,
                    "platform": token.platform,
                    "device_id": token.device_id,
                    "device_name": token.device_name
                }
                for token in tokens
            ]
        finally:
            db.close()

    async def send_to_user_devices(
        self,
        user_id: int,
        payload: Dict[str, Any],
        device_tokens: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Send push notification to all user devices"""

        if not device_tokens:
            device_tokens = await self.get_user_device_tokens(user_id)

        if not device_tokens:
            return []

        # Group tokens by platform
        android_tokens = []
        ios_tokens = []
        web_tokens = []

        for device in device_tokens:
            if device["platform"] == DevicePlatform.ANDROID:
                android_tokens.append(device)
            elif device["platform"] == DevicePlatform.IOS:
                ios_tokens.append(device)
            elif device["platform"] == DevicePlatform.WEB:
                web_tokens.append(device)

        results = []

        # Send to Android devices via FCM
        if android_tokens:
            android_token_strings = [device["token"] for device in android_tokens]
            fcm_results = await self.fcm.send_to_multiple(android_token_strings, payload)
            results.extend(fcm_results)

        # Send to iOS devices via APNS
        if ios_tokens:
            ios_token_strings = [device["token"] for device in ios_tokens]
            apns_results = await self.apns.send_to_multiple(ios_token_strings, payload)
            results.extend(apns_results)

        # Send to web devices via FCM
        if web_tokens:
            web_token_strings = [device["token"] for device in web_tokens]
            web_fcm_results = await self.fcm.send_to_multiple(web_token_strings, payload)
            results.extend(web_fcm_results)

        # Log results and update token status
        await self._log_push_results(user_id, payload, results, device_tokens)

        return results

    async def _log_push_results(
        self,
        user_id: int,
        payload: Dict[str, Any],
        results: List[Dict[str, Any]],
        device_tokens: List[Dict[str, Any]]
    ):
        """Log push notification results and update device token status"""

        db = next(get_db())
        try:
            # Create token lookup
            token_lookup = {device["token"]: device for device in device_tokens}

            for result in results:
                token = result.get("token")
                if not token:
                    continue

                device_info = token_lookup.get(token, {})
                device_token_id = device_info.get("id")

                # Create log entry
                log_entry = PushNotificationLog(
                    user_id=user_id,
                    device_token_id=device_token_id,
                    title=payload.get("title", ""),
                    body=payload.get("body", ""),
                    data=payload.get("data", {}),
                    platform=device_info.get("platform", "unknown"),
                    status="sent" if result.get("success") else "failed",
                    response_data=result,
                    error_message=result.get("error") if not result.get("success") else None
                )

                db.add(log_entry)

                # Update device token status
                if device_token_id:
                    device_token = db.query(DeviceToken).filter(
                        DeviceToken.id == device_token_id
                    ).first()

                    if device_token:
                        if result.get("success"):
                            device_token.last_used = datetime.utcnow()
                            device_token.failure_count = 0
                        else:
                            device_token.failure_count += 1
                            device_token.last_failure = datetime.utcnow()
                            device_token.failure_reason = result.get("error", "Unknown error")

                            # Deactivate token after too many failures
                            if device_token.failure_count >= 5:
                                device_token.is_active = False
                                logger.warning(f"Deactivated device token {token} after {device_token.failure_count} failures")

            db.commit()

        except Exception as e:
            logger.error(f"Failed to log push results: {e}")
            db.rollback()
        finally:
            db.close()

    @staticmethod
    async def unregister_device_token(db: Session, token: str) -> bool:
        """Unregister/deactivate device token"""
        try:
            device_token = db.query(DeviceToken).filter(
                DeviceToken.token == token
            ).first()

            if device_token:
                device_token.is_active = False
                device_token.updated_at = datetime.utcnow()
                db.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to unregister device token: {e}")
            return False

    @staticmethod
    async def get_push_statistics(user_id: int = None, days: int = 30) -> Dict[str, Any]:
        """Get push notification statistics"""
        db = next(get_db())
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            query = db.query(PushNotificationLog).filter(
                PushNotificationLog.sent_at >= since_date
            )

            if user_id:
                query = query.filter(PushNotificationLog.user_id == user_id)

            logs = query.all()

            total_sent = len(logs)
            successful_sent = sum(1 for log in logs if log.status == "sent")
            failed_sent = sum(1 for log in logs if log.status == "failed")

            # Platform breakdown
            platform_stats = {}
            for log in logs:
                platform = log.platform
                if platform not in platform_stats:
                    platform_stats[platform] = {"sent": 0, "failed": 0}

                if log.status == "sent":
                    platform_stats[platform]["sent"] += 1
                else:
                    platform_stats[platform]["failed"] += 1

            return {
                "period_days": days,
                "total_sent": total_sent,
                "successful": successful_sent,
                "failed": failed_sent,
                "success_rate": (successful_sent / total_sent * 100) if total_sent > 0 else 0,
                "platform_breakdown": platform_stats
            }

        except Exception as e:
            logger.error(f"Failed to get push statistics: {e}")
            return {"error": str(e)}
        finally:
            db.close()


# Global service instance
push_service = PushNotificationService()
