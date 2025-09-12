"""
Support Ticket Notification Service
"""

from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.support import SupportTicket, TicketResponse, TicketStatus
from app.models.user import User, UserRole
from app.services.email_service import EmailService  # Assuming this exists


class SupportNotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()

    async def notify_new_ticket(self, ticket: SupportTicket) -> None:
        """
        Send notifications for a new support ticket
        - Confirmation email to user
        - Notification to support staff
        """
        # Send confirmation to user
        await self._send_user_confirmation(ticket)
        
        # Notify support staff
        await self._notify_support_staff(ticket)

    async def notify_ticket_update(self, ticket: SupportTicket, response: TicketResponse) -> None:
        """
        Send notifications for ticket updates
        - Notify user of staff responses
        - Notify staff of user responses
        """
        if response.user.role in [UserRole.ADMIN, UserRole.MODERATOR]:
            # Staff response - notify user
            await self._notify_user_of_response(ticket, response)
        else:
            # User response - notify staff
            await self._notify_staff_of_response(ticket, response)

    async def notify_ticket_resolved(self, ticket: SupportTicket) -> None:
        """
        Send resolution notification to user
        """
        template = "support/ticket_resolved.html"
        context = {
            "user": ticket.user,
            "ticket": ticket,
            "feedback_url": f"/support/feedback/{ticket.id}"
        }
        
        await self.email_service.send_email(
            to_email=ticket.user.email,
            subject=f"Your support ticket #{ticket.id} has been resolved",
            template=template,
            context=context
        )

    async def _send_user_confirmation(self, ticket: SupportTicket) -> None:
        """Send ticket creation confirmation to user"""
        template = "support/new_ticket_confirmation.html"
        context = {
            "user": ticket.user,
            "ticket": ticket,
            "ticket_url": f"/support/tickets/{ticket.id}"
        }
        
        await self.email_service.send_email(
            to_email=ticket.user.email,
            subject=f"Support ticket #{ticket.id} received",
            template=template,
            context=context
        )

    async def _notify_support_staff(self, ticket: SupportTicket) -> None:
        """Notify support staff of new ticket"""
        # Get all support staff
        support_staff = (
            self.db.query(User)
            .filter(User.role.in_([UserRole.ADMIN, UserRole.MODERATOR]))
            .filter(User.status == 'active')
            .all()
        )

        template = "support/new_ticket_staff.html"
        context = {
            "ticket": ticket,
            "ticket_url": f"/admin/support/tickets/{ticket.id}"
        }

        # Send notifications in parallel
        for staff in support_staff:
            await self.email_service.send_email(
                to_email=staff.email,
                subject=f"New support ticket #{ticket.id}: {ticket.title}",
                template=template,
                context=context
            )

    async def _notify_user_of_response(self, ticket: SupportTicket, response: TicketResponse) -> None:
        """Notify user of staff response"""
        if not response.is_internal:  # Don't notify about internal notes
            template = "support/ticket_response.html"
            context = {
                "user": ticket.user,
                "ticket": ticket,
                "response": response,
                "ticket_url": f"/support/tickets/{ticket.id}"
            }
            
            await self.email_service.send_email(
                to_email=ticket.user.email,
                subject=f"New response to your ticket #{ticket.id}",
                template=template,
                context=context
            )

    async def _notify_staff_of_response(self, ticket: SupportTicket, response: TicketResponse) -> None:
        """Notify relevant staff members of user response"""
        # Get staff members who have previously responded to this ticket
        staff_responders = (
            self.db.query(User)
            .join(TicketResponse, User.id == TicketResponse.user_id)
            .filter(
                TicketResponse.ticket_id == ticket.id,
                User.role.in_([UserRole.ADMIN, UserRole.MODERATOR])
            )
            .distinct()
            .all()
        )

        template = "support/ticket_user_response.html"
        context = {
            "ticket": ticket,
            "response": response,
            "ticket_url": f"/admin/support/tickets/{ticket.id}"
        }

        # Notify all relevant staff members
        for staff in staff_responders:
            await self.email_service.send_email(
                to_email=staff.email,
                subject=f"New user response on ticket #{ticket.id}",
                template=template,
                context=context
            )