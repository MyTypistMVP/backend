"""
Support Ticket Notification Service
"""

from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List

from app.models.ticket import Ticket, TicketResponse, TicketStatus
from app.models.user import User, UserRole
from app.services.email import EmailService  # Using your existing email service


class TicketNotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()

    async def notify_new_ticket(self, ticket: Ticket) -> None:
        """
        Send notifications for a new support ticket
        - Confirmation email to user/guest
        - Notification to support staff
        """
        # Send confirmation to user or guest
        await self._send_ticket_confirmation(ticket)
        
        # Notify support staff
        await self._notify_support_staff(ticket)

    async def notify_ticket_update(self, ticket: Ticket, response: TicketResponse) -> None:
        """
        Send notifications for ticket updates
        - Notify user/guest of staff responses
        - Notify staff of user/guest responses
        """
        if response.is_staff_response:
            # Staff response - notify user/guest
            await self._notify_ticket_owner(ticket, response)
        else:
            # User/guest response - notify staff
            await self._notify_staff_of_response(ticket, response)

    async def notify_ticket_resolved(self, ticket: Ticket) -> None:
        """
        Send resolution notification to user/guest
        """
        template = "support/ticket_resolved.html"
        context = {
            "ticket": ticket,
            "feedback_url": f"/support/feedback/{ticket.id}"
        }
        
        if ticket.user_id:
            # Registered user
            await self.email_service.send_email(
                to_email=ticket.user.email,
                subject=f"Your support ticket #{ticket.id} has been resolved",
                template=template,
                context=context
            )
        elif ticket.guest_email:
            # Guest user
            await self.email_service.send_email(
                to_email=ticket.guest_email,
                subject=f"Your support ticket #{ticket.id} has been resolved",
                template=template,
                context=context
            )

    async def _send_ticket_confirmation(self, ticket: Ticket) -> None:
        """Send ticket creation confirmation to user/guest"""
        template = "support/new_ticket_confirmation.html"
        context = {
            "ticket": ticket,
            "ticket_url": f"/support/tickets/{ticket.id}"
        }
        
        # Add user context if available
        if ticket.user_id:
            context["user"] = ticket.user
            email = ticket.user.email
        else:
            email = ticket.guest_email
        
        if email:
            await self.email_service.send_email(
                to_email=email,
                subject=f"Support ticket #{ticket.id} received",
                template=template,
                context=context
            )

    async def _notify_support_staff(self, ticket: Ticket) -> None:
        """Notify support staff of new ticket"""
        # Get all active support staff
        support_staff = (
            self.db.query(User)
            .filter(
                User.role.in_([UserRole.ADMIN, UserRole.MODERATOR]),
                User.is_active.is_(True)
            )
            .all()
        )

        template = "support/new_ticket_staff.html"
        context = {
            "ticket": ticket,
            "ticket_url": f"/admin/support/tickets/{ticket.id}"
        }

        # Add relevant ticket metadata
        if ticket.document_id:
            context["document"] = ticket.document
        if ticket.template_id:
            context["template"] = ticket.template
        if ticket.error_details:
            context["error_details"] = ticket.error_details

        # Send notifications to all staff
        for staff in support_staff:
            await self.email_service.send_email(
                to_email=staff.email,
                subject=f"New {ticket.priority.value} priority ticket #{ticket.id}: {ticket.title}",
                template=template,
                context=context
            )

    async def _notify_ticket_owner(self, ticket: Ticket, response: TicketResponse) -> None:
        """Notify ticket owner (user/guest) of staff response"""
        template = "support/ticket_response.html"
        context = {
            "ticket": ticket,
            "response": response,
            "ticket_url": f"/support/tickets/{ticket.id}"
        }

        email = ticket.user.email if ticket.user_id else ticket.guest_email
        if email:
            await self.email_service.send_email(
                to_email=email,
                subject=f"New response to your ticket #{ticket.id}",
                template=template,
                context=context
            )

    async def _notify_staff_of_response(self, ticket: Ticket, response: TicketResponse) -> None:
        """Notify relevant staff members of user/guest response"""
        # Get staff members who have previously responded to this ticket
        staff_responders = (
            self.db.query(User)
            .join(TicketResponse, User.id == TicketResponse.user_id)
            .filter(
                TicketResponse.ticket_id == ticket.id,
                TicketResponse.is_staff_response.is_(True),
                User.is_active.is_(True)
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

        # Add user/guest context
        if ticket.user_id:
            context["user"] = ticket.user
        else:
            context["guest_email"] = ticket.guest_email

        # Notify all relevant staff members
        for staff in staff_responders:
            await self.email_service.send_email(
                to_email=staff.email,
                subject=f"New response on ticket #{ticket.id}",
                template=template,
                context=context
            )