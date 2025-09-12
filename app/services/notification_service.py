"""NotificationService adapter that exposes async APIs and delegates
to the richer `EnhancedNotificationService` when available.

This approach consolidates notification usage without immediately
deleting the existing `enhanced_notification_service.py`. Sync
implementation methods are executed in a thread using
`asyncio.to_thread`, while async implementations are awaited directly.
"""

from typing import Any, Dict, List, Optional
import asyncio
import inspect

try:
    from app.services.enhanced_notification_service import EnhancedNotificationService as _Impl
except Exception:
    _Impl = None


async def _call_impl(func, *args, **kwargs):
    if func is None:
        raise RuntimeError("No notification implementation available")

    if inspect.iscoroutinefunction(func):
        return await func(*args, **kwargs)
    else:
        return await asyncio.to_thread(func, *args, **kwargs)


class NotificationService:
    """Async facade for the notification implementation."""

    @staticmethod
    async def send_notification(user_id: int, title: str, body: str,
                                data: Optional[Dict[str, Any]] = None,
                                notification_type: str = "general",
                                priority: str = "normal",
                                expire_days: int = 30) -> bool:
        """Send/create a notification for a user."""
        if _Impl is None:
            raise RuntimeError("Notification implementation missing")

        # Enhanced implementation exposes `create_notification`
        func = getattr(_Impl, "create_notification", None) or getattr(_Impl, "send_notification", None)
        return await _call_impl(func, None, user_id, notification_type, title, body, priority, ["in_app"], data)

    @staticmethod
    async def get_user_notifications(user_id: int, unread_only: bool = False,
                                     notification_type: Optional[str] = None,
                                     limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        if _Impl is None:
            raise RuntimeError("Notification implementation missing")

        func = getattr(_Impl, "get_user_notifications", None)
        return await _call_impl(func, None, user_id, limit, limit, unread_only, notification_type)

    @staticmethod
    async def mark_as_read(user_id: int, notification_ids: List[int]) -> Dict[str, Any]:
        if _Impl is None:
            raise RuntimeError("Notification implementation missing")

        func = getattr(_Impl, "mark_as_read", None)
        return await _call_impl(func, None, notification_ids, user_id)

    @staticmethod
    async def delete_notifications(user_id: int, notification_ids: List[int]) -> Dict[str, Any]:
        if _Impl is None:
            raise RuntimeError("Notification implementation missing")

        # Enhanced service has `dismiss_notification` and `mark_all_as_read`; prefer a delete-style API
        func = getattr(_Impl, "dismiss_notification", None) or getattr(_Impl, "delete_notifications", None)
        # If the implementation expects (db, notification_id, user_id), we call for each id
        results = []
        for nid in notification_ids:
            r = await _call_impl(func, None, nid, user_id)
            results.append(r)

        # Summarize
        deleted = sum(1 for r in results if r is True or (isinstance(r, dict) and r.get("deleted", 0) > 0))
        return {"success": True, "deleted": deleted}

    @staticmethod
    async def create_from_template(user_id: int, notification_type: str, template_data: Optional[Dict[str, Any]] = None):
        if _Impl is None:
            raise RuntimeError("Notification implementation missing")

        func = getattr(_Impl, "create_from_template", None) or getattr(_Impl, "create_notification", None)
        return await _call_impl(func, None, user_id, notification_type, template_data)

    @staticmethod
    async def deliver_notification(notification_id: int):
        if _Impl is None:
            raise RuntimeError("Notification implementation missing")

        func = getattr(_Impl, "deliver_notification", None)
        return await _call_impl(func, None, notification_id)
