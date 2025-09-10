"""
Comprehensive Admin Dashboard Service
Handles all statistics, analytics, and administrative functions
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, func, desc, and_, or_
from database import Base
from app.models.user import User
from app.models.template import Template
from app.models.document import Document
from app.models.payment import Payment

logger = logging.getLogger(__name__)


class AdminDashboardService:
    """Service for admin dashboard analytics and management"""

    @staticmethod
    async def get_realtime_stats(db: Session) -> Dict[str, Any]:
        """Get real-time statistics for admin dashboard"""
        try:
            # Active users in last 15 minutes
            fifteen_mins_ago = datetime.utcnow() - timedelta(minutes=15)
            active_users = db.query(PageVisit).filter(
                PageVisit.created_at >= fifteen_mins_ago
            ).distinct(PageVisit.user_id).count()

            # Documents being created/processed now
            processing_docs = db.query(Document).filter(
                Document.status == "processing",
                Document.created_at >= fifteen_mins_ago
            ).count()

            # Current revenue today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_revenue = db.query(func.sum(Payment.amount)).filter(
                Payment.status == "completed",
                Payment.created_at >= today_start
            ).scalar() or 0.0

            return {
                "active_users_now": active_users,
                "processing_documents": processing_docs,
                "revenue_today": today_revenue,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get realtime stats: {e}")
            raise

    @staticmethod
    async def get_daily_summary(db: Session, date: datetime) -> Dict[str, Any]:
        """Get or generate daily analytics summary"""
        try:
            # Try to get existing summary
            summary = db.query(AnalyticsSummary).filter(
                func.date(AnalyticsSummary.date) == date.date()
            ).first()

            if summary:
                return json.loads(summary.top_pages) if summary.top_pages else {}

            # Generate new summary
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            # User metrics
            new_users = db.query(User).filter(
                User.created_at.between(start_of_day, end_of_day)
            ).count()

            active_users = db.query(PageVisit).filter(
                PageVisit.created_at.between(start_of_day, end_of_day)
            ).distinct(PageVisit.user_id).count()

            # Document metrics
            docs_created = db.query(Document).filter(
                Document.created_at.between(start_of_day, end_of_day)
            ).count()

            # Revenue metrics
            revenue = db.query(func.sum(Payment.amount)).filter(
                Payment.status == "completed",
                Payment.created_at.between(start_of_day, end_of_day)
            ).scalar() or 0.0

            # Visit metrics
            visits = db.query(PageVisit).filter(
                PageVisit.created_at.between(start_of_day, end_of_day)
            ).all()
            
            # Create summary record
            summary = AnalyticsSummary(
                date=date,
                total_users=db.query(User).count(),
                new_users=new_users,
                active_users=active_users,
                documents_created=docs_created,
                revenue_amount=revenue,
                total_visits=len(visits),
                unique_visitors=len(set(v.session_id for v in visits)),
                avg_visit_duration=sum(v.visit_duration for v in visits) / len(visits) if visits else 0
            )
            
            db.add(summary)
            await db.commit()
            await db.refresh(summary)
            
            return {
                "date": date.isoformat(),
                "metrics": {
                    "users": {
                        "total": summary.total_users,
                        "new": summary.new_users,
                        "active": summary.active_users
                    },
                    "documents": {
                        "created": summary.documents_created,
                        "downloaded": summary.documents_downloaded
                    },
                    "revenue": {
                        "total": summary.revenue_amount,
                        "currency": summary.revenue_currency
                    },
                    "visits": {
                        "total": summary.total_visits,
                        "unique": summary.unique_visitors,
                        "avg_duration": summary.avg_visit_duration
                    }
                }
            }
        except Exception as e:
            logger.error(f"Failed to generate daily summary: {e}")
            raise


class PageVisit(Base):
    """Track page visits for analytics"""
    __tablename__ = "page_visits"

    id = Column(Integer, primary_key=True, index=True)
    page_path = Column(String(500), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(String(500), nullable=True)
    visit_duration = Column(Integer, default=0)  # seconds
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Analytics data
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    browser = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)


class AnalyticsSummary(Base):
    """Daily analytics summary for quick dashboard access"""
    __tablename__ = "analytics_summaries"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # User metrics
    total_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    
    # Document metrics
    documents_created = Column(Integer, default=0)
    documents_downloaded = Column(Integer, default=0)
    template_submissions = Column(Integer, default=0)
    
    # Revenue metrics
    revenue_amount = Column(Float, default=0.0)
    revenue_currency = Column(String(3), default="NGN")
    subscription_revenue = Column(Float, default=0.0)
    pay_as_you_go_revenue = Column(Float, default=0.0)
    
    # Visit metrics
    total_visits = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    avg_visit_duration = Column(Float, default=0.0)  # seconds
    bounce_rate = Column(Float, default=0.0)  # percentage
    
    # Most visited pages (JSON array of {path, count})
    top_pages = Column(Text, nullable=True)
    
    # Performance metrics
    avg_response_time = Column(Float, default=0.0)  # milliseconds
    error_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentShare(Base):
    """Document sharing with time-limited access"""
    __tablename__ = "document_shares"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, index=True)
    shared_by = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    share_token = Column(String(100), unique=True, nullable=False, index=True)
    share_password = Column(String(255), nullable=True)  # Auto-generated password

    # Access control
    expires_at = Column(DateTime, nullable=False, index=True)
    max_views = Column(Integer, default=None)  # Optional view limit
    current_views = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)
    access_log = Column(Text, nullable=True)  # JSON log of access attempts


class AdminDashboardService:
    """Comprehensive admin dashboard with all statistics and management functions"""

    @staticmethod
    def get_comprehensive_dashboard_stats(db: Session) -> Dict[str, Any]:
        """
        Get all dashboard statistics including earnings, customers, visits, and analytics
        """
        try:
            # Time ranges for analytics
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)

            # User Statistics
            total_users = db.query(User).count()
            new_users_today = db.query(User).filter(
                func.date(User.created_at) == today
            ).count()
            new_users_week = db.query(User).filter(
                func.date(User.created_at) >= week_ago
            ).count()
            new_users_month = db.query(User).filter(
                func.date(User.created_at) >= month_ago
            ).count()

            # Active users (visited in last 7 days)
            active_users = db.query(PageVisit).filter(
                PageVisit.created_at >= datetime.utcnow() - timedelta(days=7),
                PageVisit.user_id.isnot(None)
            ).distinct(PageVisit.user_id).count()

            # Document Statistics
            total_documents = db.query(Document).count()
            documents_today = db.query(Document).filter(
                func.date(Document.created_at) == today
            ).count()
            documents_week = db.query(Document).filter(
                func.date(Document.created_at) >= week_ago
            ).count()
            documents_month = db.query(Document).filter(
                func.date(Document.created_at) >= month_ago
            ).count()

            # Template Statistics
            total_templates = db.query(Template).count()
            active_templates = db.query(Template).filter(
                Template.is_active == True
            ).count()

            # Payment/Revenue Statistics
            total_revenue = db.query(func.sum(Payment.amount)).filter(
                Payment.status == "completed"
            ).scalar() or 0

            revenue_today = db.query(func.sum(Payment.amount)).filter(
                Payment.status == "completed",
                func.date(Payment.created_at) == today
            ).scalar() or 0

            revenue_week = db.query(func.sum(Payment.amount)).filter(
                Payment.status == "completed",
                func.date(Payment.created_at) >= week_ago
            ).scalar() or 0

            revenue_month = db.query(func.sum(Payment.amount)).filter(
                Payment.status == "completed",
                func.date(Payment.created_at) >= month_ago
            ).scalar() or 0

            # Page Visit Statistics
            total_visits = db.query(PageVisit).count()
            visits_today = db.query(PageVisit).filter(
                func.date(PageVisit.created_at) == today
            ).count()
            visits_week = db.query(PageVisit).filter(
                func.date(PageVisit.created_at) >= week_ago
            ).count()

            # Average visit duration
            avg_visit_duration = db.query(func.avg(PageVisit.visit_duration)).filter(
                PageVisit.visit_duration > 0
            ).scalar() or 0

            # Most visited pages
            popular_pages = db.query(
                PageVisit.page_path,
                func.count(PageVisit.id).label('visit_count')
            ).group_by(PageVisit.page_path).order_by(
                desc('visit_count')
            ).limit(10).all()

            # User role distribution
            role_distribution = db.query(
                User.role,
                func.count(User.id).label('count')
            ).group_by(User.role).all()

            # Recent activity
            recent_users = db.query(User).order_by(desc(User.created_at)).limit(5).all()
            recent_documents = db.query(Document).order_by(desc(Document.created_at)).limit(5).all()
            recent_payments = db.query(Payment).order_by(desc(Payment.created_at)).limit(5).all()

            # Device and browser analytics
            device_stats = db.query(
                PageVisit.device_type,
                func.count(PageVisit.id).label('count')
            ).filter(
                PageVisit.device_type.isnot(None)
            ).group_by(PageVisit.device_type).all()

            browser_stats = db.query(
                PageVisit.browser,
                func.count(PageVisit.id).label('count')
            ).filter(
                PageVisit.browser.isnot(None)
            ).group_by(PageVisit.browser).limit(10).all()

            return {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "overview": {
                    "total_users": total_users,
                    "total_documents": total_documents,
                    "total_templates": total_templates,
                    "total_revenue": float(total_revenue),
                    "total_visits": total_visits,
                    "active_users": active_users,
                    "active_templates": active_templates
                },
                "growth": {
                    "users": {
                        "today": new_users_today,
                        "week": new_users_week,
                        "month": new_users_month
                    },
                    "documents": {
                        "today": documents_today,
                        "week": documents_week,
                        "month": documents_month
                    },
                    "revenue": {
                        "today": float(revenue_today),
                        "week": float(revenue_week),
                        "month": float(revenue_month)
                    },
                    "visits": {
                        "today": visits_today,
                        "week": visits_week,
                        "average_duration": float(avg_visit_duration)
                    }
                },
                "analytics": {
                    "popular_pages": [
                        {"page": page, "visits": count}
                        for page, count in popular_pages
                    ],
                    "user_roles": [
                        {"role": role, "count": count}
                        for role, count in role_distribution
                    ],
                    "devices": [
                        {"device": device, "count": count}
                        for device, count in device_stats
                    ],
                    "browsers": [
                        {"browser": browser, "count": count}
                        for browser, count in browser_stats
                    ]
                },
                "recent_activity": {
                    "users": [
                        {
                            "id": user.id,
                            "email": user.email,
                            "role": user.role,
                            "created_at": user.created_at.isoformat() if user.created_at else None
                        }
                        for user in recent_users
                    ],
                    "documents": [
                        {
                            "id": doc.id,
                            "title": doc.title,
                            "user_id": doc.user_id,
                            "created_at": doc.created_at.isoformat() if doc.created_at else None
                        }
                        for doc in recent_documents
                    ],
                    "payments": [
                        {
                            "id": payment.id,
                            "amount": float(payment.amount),
                            "status": payment.status,
                            "user_id": payment.user_id,
                            "created_at": payment.created_at.isoformat() if payment.created_at else None
                        }
                        for payment in recent_payments
                    ]
                }
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard stats: {e}")
            raise

    @staticmethod
    def track_page_visit(
        db: Session,
        page_path: str,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Track page visits for analytics"""
        try:
            visit = PageVisit(
                page_path=page_path,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
                device_type=device_info.get("device_type") if device_info else None,
                browser=device_info.get("browser") if device_info else None,
                country=device_info.get("country") if device_info else None,
                city=device_info.get("city") if device_info else None
            )

            db.add(visit)
            db.commit()
            db.refresh(visit)

            return {
                "success": True,
                "visit_id": visit.id,
                "message": "Page visit tracked"
            }

        except Exception as e:
            logger.error(f"Failed to track page visit: {e}")
            raise

    @staticmethod
    def create_document_share(
        db: Session,
        document_id: int,
        shared_by: int,
        hours_valid: int = 5,
        max_views: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a time-limited shareable link for document preview
        """
        try:
            import secrets
            import string

            # Generate secure share token
            share_token = ''.join(secrets.choice(
                string.ascii_letters + string.digits
            ) for _ in range(32))

            # Generate auto password
            password = ''.join(secrets.choice(
                string.ascii_uppercase + string.digits
            ) for _ in range(8))

            # Calculate expiration
            expires_at = datetime.utcnow() + timedelta(hours=hours_valid)

            # Create share record
            share = DocumentShare(
                document_id=document_id,
                shared_by=shared_by,
                share_token=share_token,
                share_password=password,
                expires_at=expires_at,
                max_views=max_views
            )

            db.add(share)
            db.commit()
            db.refresh(share)

            # Generate shareable URL
            share_url = f"/shared/{share_token}"

            logger.info(f"Document share created: {share.id} for document {document_id}")

            return {
                "success": True,
                "share_id": share.id,
                "share_token": share_token,
                "share_url": share_url,
                "password": password,
                "expires_at": expires_at.isoformat(),
                "expires_in_hours": hours_valid,
                "max_views": max_views,
                "message": f"Document share link created. Valid for {hours_valid} hours."
            }

        except Exception as e:
            logger.error(f"Failed to create document share: {e}")
            raise

    @staticmethod
    def access_shared_document(
        db: Session,
        share_token: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Access a shared document with token and password
        """
        try:
            # Find share record
            share = db.query(DocumentShare).filter(
                DocumentShare.share_token == share_token,
                DocumentShare.is_active == True
            ).first()

            if not share:
                return {
                    "success": False,
                    "error": "Share link not found or expired"
                }

            # Check expiration
            if datetime.utcnow() > share.expires_at:
                share.is_active = False
                db.commit()
                return {
                    "success": False,
                    "error": "Share link has expired"
                }

            # Check password
            if share.share_password and share.share_password != password:
                # Log failed access attempt
                access_log = json.loads(share.access_log) if share.access_log else []
                access_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "ip_address": ip_address,
                    "status": "failed_password",
                    "error": "Invalid password"
                })
                share.access_log = json.dumps(access_log)
                db.commit()

                return {
                    "success": False,
                    "error": "Invalid password"
                }

            # Check view limit
            if share.max_views and share.current_views >= share.max_views:
                return {
                    "success": False,
                    "error": "Maximum views reached"
                }

            # Get document
            document = db.query(Document).filter(
                Document.id == share.document_id
            ).first()

            if not document:
                return {
                    "success": False,
                    "error": "Document not found"
                }

            # Update access tracking
            share.current_views += 1
            share.last_accessed = datetime.utcnow()

            # Log successful access
            access_log = json.loads(share.access_log) if share.access_log else []
            access_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "ip_address": ip_address,
                "status": "success",
                "view_number": share.current_views
            })
            share.access_log = json.dumps(access_log)

            db.commit()

            return {
                "success": True,
                "document": {
                    "id": document.id,
                    "title": document.title,
                    "content": document.content,
                    "file_path": document.file_path,
                    "created_at": document.created_at.isoformat() if document.created_at else None
                },
                "share_info": {
                    "expires_at": share.expires_at.isoformat(),
                    "views_remaining": (share.max_views - share.current_views) if share.max_views else None,
                    "current_views": share.current_views
                },
                "view_only": True,
                "message": "Document accessed successfully"
            }

        except Exception as e:
            logger.error(f"Failed to access shared document: {e}")
            raise

    @staticmethod
    def get_page_analytics(
        db: Session,
        days: int = 30,
        page_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed page analytics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            query = db.query(PageVisit).filter(
                PageVisit.created_at >= start_date
            )

            if page_path:
                query = query.filter(PageVisit.page_path == page_path)

            visits = query.all()

            # Calculate analytics
            total_visits = len(visits)
            unique_visitors = len(set(v.user_id for v in visits if v.user_id))
            unique_sessions = len(set(v.session_id for v in visits if v.session_id))

            # Average visit duration
            durations = [v.visit_duration for v in visits if v.visit_duration > 0]
            avg_duration = sum(durations) / len(durations) if durations else 0

            # Daily breakdown
            daily_stats = {}
            for visit in visits:
                date_key = visit.created_at.date().isoformat()
                if date_key not in daily_stats:
                    daily_stats[date_key] = {"visits": 0, "unique_users": set()}
                daily_stats[date_key]["visits"] += 1
                if visit.user_id:
                    daily_stats[date_key]["unique_users"].add(visit.user_id)

            # Convert sets to counts
            for date_key in daily_stats:
                daily_stats[date_key]["unique_users"] = len(daily_stats[date_key]["unique_users"])

            # Top referrers
            referrer_stats = {}
            for visit in visits:
                if visit.referrer:
                    referrer_stats[visit.referrer] = referrer_stats.get(visit.referrer, 0) + 1

            top_referrers = sorted(referrer_stats.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                "success": True,
                "period_days": days,
                "page_path": page_path,
                "summary": {
                    "total_visits": total_visits,
                    "unique_visitors": unique_visitors,
                    "unique_sessions": unique_sessions,
                    "average_duration_seconds": round(avg_duration, 2),
                    "bounce_rate": 0  # Would need additional tracking for this
                },
                "daily_breakdown": daily_stats,
                "top_referrers": [
                    {"referrer": ref, "visits": count}
                    for ref, count in top_referrers
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get page analytics: {e}")
            raise

    @staticmethod
    def get_user_management_data(
        db: Session,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
        role_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive user management data for admin
        """
        try:
            query = db.query(User)

            # Apply filters
            if search:
                query = query.filter(or_(
                    User.email.ilike(f"%{search}%"),
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%")
                ))

            if role_filter:
                query = query.filter(User.role == role_filter)

            # Get total count
            total_users = query.count()

            # Apply pagination
            offset = (page - 1) * limit
            users = query.offset(offset).limit(limit).all()

            # Get additional user statistics
            user_data = []
            for user in users:
                # Get user's document count
                doc_count = db.query(Document).filter(Document.user_id == user.id).count()

                # Get user's total spending
                total_spent = db.query(func.sum(Payment.amount)).filter(
                    Payment.user_id == user.id,
                    Payment.status == "completed"
                ).scalar() or 0

                # Get last activity
                last_visit = db.query(PageVisit).filter(
                    PageVisit.user_id == user.id
                ).order_by(desc(PageVisit.created_at)).first()

                user_data.append({
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "document_count": doc_count,
                    "total_spent": float(total_spent),
                    "last_visit": last_visit.created_at.isoformat() if last_visit else None
                })

            return {
                "success": True,
                "users": user_data,
                "pagination": {
                    "total": total_users,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total_users + limit - 1) // limit
                }
            }

        except Exception as e:
            logger.error(f"Failed to get user management data: {e}")
            raise
