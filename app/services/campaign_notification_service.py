"""Campaign notification service"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.token_management_service import TokenManagementService
from app.models.user import User
from app.services.notification_service import NotificationService
from app.models.token import TokenType
import json
import logging

logger = logging.getLogger(__name__)


class CampaignNotificationService:
    """Service for handling campaign notifications and messages"""

    @staticmethod
    async def send_campaign_notification(
        user_id: int,
        campaign_id: int,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        notification_type: str = "campaign",
        priority: str = "normal"
    ):
        """Send a campaign notification to a user"""
        try:
            await NotificationService.send_notification(
                user_id=user_id,
                title="Campaign Update",
                body=message,
                data={
                    "campaign_id": campaign_id,
                    "type": notification_type,
                    **data
                } if data else {"campaign_id": campaign_id, "type": notification_type},
                priority=priority
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send campaign notification: {e}")
            return False

    @staticmethod
    async def notify_campaign_reward(
        user_id: int,
        campaign_id: int,
        reward_amount: int,
        token_type: TokenType
    ):
        """Send notification about campaign reward"""
        try:
            message = f"Congratulations! You've earned {reward_amount} {token_type.value} tokens!"
            await CampaignNotificationService.send_campaign_notification(
                user_id=user_id,
                campaign_id=campaign_id,
                message=message,
                data={
                    "reward_amount": reward_amount,
                    "token_type": token_type.value
                },
                notification_type="campaign_reward"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send reward notification: {e}")
            return False

    @staticmethod
    async def notify_campaign_milestone(
        user_id: int,
        campaign_id: int,
        milestone: str,
        achievement: Any
    ):
        """Send notification about campaign milestone"""
        try:
            message = f"Achievement unlocked: {milestone}!"
            await CampaignNotificationService.send_campaign_notification(
                user_id=user_id,
                campaign_id=campaign_id,
                message=message,
                data={
                    "milestone": milestone,
                    "achievement": achievement
                },
                notification_type="campaign_milestone"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send milestone notification: {e}")
            return False

    @staticmethod
    async def notify_campaign_start(
        users: List[User],
        campaign_id: int,
        campaign_name: str,
        campaign_details: Dict[str, Any]
    ):
        """Notify users about campaign start"""
        failures = []
        for user in users:
            try:
                message = f"New campaign started: {campaign_name}"
                success = await CampaignNotificationService.send_campaign_notification(
                    user_id=user.id,
                    campaign_id=campaign_id,
                    message=message,
                    data=campaign_details,
                    notification_type="campaign_start"
                )
                if not success:
                    failures.append(user.id)
            except Exception:
                failures.append(user.id)

        return {
            "total": len(users),
            "succeeded": len(users) - len(failures),
            "failed": len(failures),
            "failed_users": failures
        }

    @staticmethod
    async def notify_campaign_end(
        users: List[User],
        campaign_id: int,
        campaign_name: str,
        campaign_summary: Dict[str, Any]
    ):
        """Notify users about campaign end"""
        failures = []
        for user in users:
            try:
                message = f"Campaign ended: {campaign_name}"
                success = await CampaignNotificationService.send_campaign_notification(
                    user_id=user.id,
                    campaign_id=campaign_id,
                    message=message,
                    data=campaign_summary,
                    notification_type="campaign_end"
                )
                if not success:
                    failures.append(user.id)
            except Exception:
                failures.append(user.id)

        return {
            "total": len(users),
            "succeeded": len(users) - len(failures),
            "failed": len(failures),
            "failed_users": failures
        }