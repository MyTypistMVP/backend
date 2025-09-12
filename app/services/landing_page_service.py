"""
Landing Page Service
Seamless guest to registration workflow with free document creation
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, desc, func
from database import Base

logger = logging.getLogger(__name__)


class LandingPageVisit(Base):
    """Enhanced tracking for landing page visits and conversions with real-time analytics"""
    __tablename__ = "landing_page_visits"

    id = Column(Integer, primary_key=True, index=True)

    # Core visitor tracking
    session_id = Column(String(100), nullable=False, index=True)
    device_fingerprint = Column(String(64), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Enhanced device info
    browser_name = Column(String(100), nullable=True)
    browser_version = Column(String(50), nullable=True)
    os_name = Column(String(100), nullable=True)
    os_version = Column(String(50), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, tablet, desktop
    screen_resolution = Column(String(50), nullable=True)
    
    # Traffic source and campaign tracking
    referrer = Column(String(500), nullable=True)
    referrer_domain = Column(String(255), nullable=True, index=True)
    utm_source = Column(String(100), nullable=True, index=True)
    utm_medium = Column(String(100), nullable=True, index=True)
    utm_campaign = Column(String(100), nullable=True, index=True)
    utm_term = Column(String(100), nullable=True)
    utm_content = Column(String(100), nullable=True)
    
    # Geo-location data
    country = Column(String(2), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)

    # Enhanced engagement tracking
    entry_page = Column(String(500), nullable=True)  # First page visited
    exit_page = Column(String(500), nullable=True)  # Last page before leaving
    pages_viewed = Column(Text, nullable=True)  # JSON array of viewed pages with timestamps
    scroll_depth = Column(Integer, default=0)  # Maximum scroll percentage
    clicks_count = Column(Integer, default=0)  # Total click interactions
    
    # Template interaction tracking
    viewed_templates = Column(Text, nullable=True)  # JSON array of {template_id, timestamp, view_duration}
    searched_terms = Column(Text, nullable=True)  # JSON array of {term, timestamp, results_count}
    template_interactions = Column(Text, nullable=True)  # JSON array of {template_id, action_type, timestamp}
    
    # Form interaction tracking
    form_interactions = Column(Text, nullable=True)  # JSON array of {field_id, action, timestamp}
    form_completion = Column(Float, default=0)  # Percentage of form completed
    form_abandonment = Column(Boolean, default=False)  # Whether user abandoned form
    last_interaction_field = Column(String(100), nullable=True)  # Last form field interacted with
    
    # Conversion funnel
    funnel_stage = Column(String(50), nullable=True, index=True)  # Current stage in conversion funnel
    created_document = Column(Boolean, default=False)
    registered = Column(Boolean, default=False)
    downloaded_document = Column(Boolean, default=False)
    converted_to_paid = Column(Boolean, default=False)
    
    # Session metrics
    time_on_page_seconds = Column(Integer, default=0)
    templates_viewed_count = Column(Integer, default=0)
    searches_performed = Column(Integer, default=0)
    bounce = Column(Boolean, default=True)  # True if left without interaction
    session_quality_score = Column(Float, default=0)  # Calculated engagement score
    
    # A/B testing
    ab_test_group = Column(String(50), nullable=True, index=True)  # A/B test group assignment
    ab_test_variant = Column(String(50), nullable=True)  # Specific variant shown
    
    # Timestamps and status
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    first_interaction_at = Column(DateTime, nullable=True)  # First meaningful interaction
    last_interaction_at = Column(DateTime, nullable=True)  # Last meaningful interaction
    converted_at = Column(DateTime, nullable=True)  # When they registered
    session_end_at = Column(DateTime, nullable=True)  # When session ended


class LandingPageTemplate(Base):
    """Popular templates for landing page display with enhanced SEO and preview capabilities"""
    __tablename__ = "landing_page_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('templates.id', ondelete='CASCADE'), nullable=False, index=True)

    # Display settings
    display_order = Column(Integer, default=0, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    landing_title = Column(String(200), nullable=True)  # Custom title for landing page
    landing_description = Column(Text, nullable=True)  # Custom description
    
    # SEO Metadata
    meta_title = Column(String(200), nullable=True)  # SEO-optimized title
    meta_description = Column(String(500), nullable=True)  # SEO meta description
    meta_keywords = Column(String(500), nullable=True)  # SEO keywords
    og_title = Column(String(200), nullable=True)  # OpenGraph title
    og_description = Column(String(500), nullable=True)  # OpenGraph description
    canonical_url = Column(String(500), nullable=True)  # Canonical URL for SEO

    # Preview settings
    preview_image_url = Column(String(500), nullable=True)  # Admin uploaded preview
    watermark_image_url = Column(String(500), nullable=True)  # Watermark for guest preview
    preview_template_file = Column(String(500), nullable=True)  # Admin's preview template file
    extraction_template_file = Column(String(500), nullable=True)  # Template for actual extraction
    demo_data = Column(Text, nullable=True)  # JSON with sample data for preview
    preview_settings = Column(Text, nullable=True)  # JSON with preview customization (watermark position, opacity, etc.)
    auto_suggest_data = Column(Text, nullable=True)  # JSON with autosuggest data for input fields

    # Analytics and tracking
    views_count = Column(Integer, default=0)
    conversions_count = Column(Integer, default=0)  # How many led to registration
    bounce_count = Column(Integer, default=0)  # How many left without interaction
    avg_time_to_convert = Column(Float, default=0)  # Average time to complete registration
    completion_rate = Column(Float, default=0)  # % of started docs that complete
    
    # Social proof
    total_documents_created = Column(Integer, default=0)  # Total docs created from this template
    avg_rating = Column(Float, default=0)  # Average user rating
    review_count = Column(Integer, default=0)  # Number of reviews
    last_used_at = Column(DateTime, nullable=True)  # Last time template was used
    
    # Performance optimization
    cache_key = Column(String(100), nullable=True, index=True)  # For efficient caching
    cache_updated_at = Column(DateTime, nullable=True)  # Last cache update

    # Status and timestamps
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=True, index=True)  # Whether visible to guests
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Security and rate limiting
    max_daily_uses = Column(Integer, default=1000)  # Prevent abuse
    current_daily_uses = Column(Integer, default=0)
    rate_limit_reset_at = Column(DateTime, nullable=True)


class LandingPageService:
    """Service for managing landing page experience and conversions"""

    @staticmethod
    def track_landing_visit(
        db: Session,
        session_id: str,
        device_fingerprint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        utm_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Track a new landing page visit"""
        try:
            # Check if visit already exists for this session
            existing_visit = db.query(LandingPageVisit).filter(
                LandingPageVisit.session_id == session_id
            ).first()

            if existing_visit:
                return {
                    "success": True,
                    "visit_id": existing_visit.id,
                    "existing_visit": True
                }

            # Create new visit record
            utm_params = utm_params or {}

            visit = LandingPageVisit(
                session_id=session_id,
                device_fingerprint=device_fingerprint,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
                utm_source=utm_params.get("utm_source"),
                utm_medium=utm_params.get("utm_medium"),
                utm_campaign=utm_params.get("utm_campaign")
            )

            db.add(visit)
            db.commit()
            db.refresh(visit)

            logger.info(f"Landing page visit tracked: {visit.id} for session {session_id}")

            return {
                "success": True,
                "visit_id": visit.id,
                "existing_visit": False,
                "session_id": session_id
            }

        except Exception as e:
            logger.error(f"Failed to track landing visit: {e}")
            raise

    @staticmethod
    def get_landing_templates(
        db: Session,
        limit: int = 12,
        featured_only: bool = False
    ) -> Dict[str, Any]:
        """Get templates to display on landing page"""
        try:
            query = db.query(LandingPageTemplate).filter(
                LandingPageTemplate.is_active == True
            )

            if featured_only:
                query = query.filter(LandingPageTemplate.is_featured == True)

            landing_templates = query.order_by(
                LandingPageTemplate.display_order,
                desc(LandingPageTemplate.conversions_count)
            ).limit(limit).all()

            # Get actual template details
            from app.models.template import Template

            templates_data = []
            for landing_template in landing_templates:
                template = db.query(Template).filter(
                    Template.id == landing_template.template_id
                ).first()

                if template:
                    # Parse demo data for preview
                    demo_data = {}
                    if landing_template.demo_data:
                        try:
                            demo_data = json.loads(landing_template.demo_data)
                        except:
                            pass

                    templates_data.append({
                        "template_id": template.id,
                        "name": landing_template.landing_title or template.name,
                        "description": landing_template.landing_description or template.description,
                        "category": template.category,
                        "price_tokens": template.price or 0,
                        "is_free": template.price == 0 or template.price is None,
                        "preview_image": landing_template.preview_image_url or f"/api/templates/{template.id}/preview",
                        "views_count": landing_template.views_count,
                        "rating": 4.5,  # Would come from actual ratings
                        "demo_data": demo_data,
                        "is_featured": landing_template.is_featured,
                        "estimated_time_minutes": LandingPageService._estimate_completion_time(template)
                    })

            return {
                "success": True,
                "templates": templates_data,
                "total_count": len(templates_data),
                "featured_count": len([t for t in templates_data if t["is_featured"]])
            }

        except Exception as e:
            logger.error(f"Failed to get landing templates: {e}")
            raise

    @staticmethod
    def search_landing_templates(
        db: Session,
        search_term: str,
        session_id: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Search templates on landing page"""
        try:
            # Track search
            LandingPageService._track_search_activity(db, session_id, search_term)

            # Perform search
            from app.models.template import Template

            # Simple search implementation (can be enhanced with full-text search)
            search_results = db.query(Template).filter(
                (Template.name.ilike(f"%{search_term}%")) |
                (Template.description.ilike(f"%{search_term}%")) |
                (Template.category.ilike(f"%{search_term}%"))
            ).limit(limit).all()

            # Get landing page settings for these templates
            template_ids = [t.id for t in search_results]
            landing_settings = db.query(LandingPageTemplate).filter(
                LandingPageTemplate.template_id.in_(template_ids),
                LandingPageTemplate.is_active == True
            ).all()

            landing_map = {ls.template_id: ls for ls in landing_settings}

            # Format results
            results_data = []
            for template in search_results:
                landing_template = landing_map.get(template.id)

                results_data.append({
                    "template_id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "category": template.category,
                    "price_tokens": template.price or 0,
                    "is_free": template.price == 0 or template.price is None,
                    "preview_image": landing_template.preview_image_url if landing_template else f"/api/templates/{template.id}/preview",
                    "is_featured": landing_template.is_featured if landing_template else False,
                    "estimated_time_minutes": LandingPageService._estimate_completion_time(template),
                    "relevance_score": LandingPageService._calculate_relevance(template, search_term)
                })

            # Sort by relevance
            results_data.sort(key=lambda x: x["relevance_score"], reverse=True)

            return {
                "success": True,
                "search_term": search_term,
                "results": results_data,
                "total_count": len(results_data),
                "suggestions": LandingPageService._get_search_suggestions(db, search_term)
            }

        except Exception as e:
            logger.error(f"Failed to search landing templates: {e}")
            raise

    @staticmethod
    def track_template_view(
        db: Session,
        template_id: int,
        session_id: str
    ) -> Dict[str, Any]:
        """Track when a user views a template preview"""
        try:
            # Update landing page visit
            visit = db.query(LandingPageVisit).filter(
                LandingPageVisit.session_id == session_id
            ).first()

            if visit:
                # Update viewed templates
                viewed_templates = []
                if visit.viewed_templates:
                    try:
                        viewed_templates = json.loads(visit.viewed_templates)
                    except:
                        pass

                if template_id not in viewed_templates:
                    viewed_templates.append(template_id)
                    visit.viewed_templates = json.dumps(viewed_templates)
                    visit.templates_viewed_count = len(viewed_templates)
                    db.commit()

            # Update landing template stats
            landing_template = db.query(LandingPageTemplate).filter(
                LandingPageTemplate.template_id == template_id,
                LandingPageTemplate.is_active == True
            ).first()

            if landing_template:
                landing_template.views_count += 1
                db.commit()

            return {
                "success": True,
                "template_id": template_id,
                "view_tracked": True
            }

        except Exception as e:
            logger.error(f"Failed to track template view: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def initiate_free_document_creation(
        db: Session,
        template_id: int,
        session_id: str,
        device_fingerprint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> Dict[str, Any]:
        """Start free document creation process for guest with enhanced security"""
        try:
            # Enhanced fraud prevention
                from app.services.fraud_detection_service import FraudDetectionService
            
                fraud_check = FraudDetectionService.check_free_token_eligibility(
                db=db,
                user_id=None,
                session_id=session_id,
                device_fingerprint=device_fingerprint,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
                additional_checks={
                    "rate_limit": True,
                    "ip_reputation": True,
                    "device_reputation": True,
                    "behavior_analysis": True
                }
            )

            if not fraud_check["eligible"]:
                return {
                    "success": False,
                    "error": "free_token_used",
                    "message": "You have already used your free document creation. Please register to continue.",
                    "redirect_to_registration": True
                }

            # Create draft for guest
            from app.services.draft_system_service import DraftSystemService

            # Get template details
            from app.models.template import Template
            template = db.query(Template).filter(Template.id == template_id).first()

            if not template:
                return {"success": False, "error": "Template not found"}

            # Create draft
            draft_result = DraftSystemService.create_draft(
                db=db,
                template_id=template_id,
                title=f"Free Document - {template.name}",
                user_id=None,
                session_id=session_id,
                device_fingerprint=device_fingerprint,
                is_free_eligible=True
            )

            if not draft_result["success"]:
                return draft_result

            # Track document creation start
            visit = db.query(LandingPageVisit).filter(
                LandingPageVisit.session_id == session_id
            ).first()

            if visit:
                visit.created_document = True
                db.commit()

            logger.info(f"Free document creation initiated: draft {draft_result['draft_id']} for template {template_id}")

            return {
                "success": True,
                "draft_id": draft_result["draft_id"],
                "template_id": template_id,
                "template_name": template.name,
                "is_free": True,
                "next_step": "fill_form",
                "form_url": f"/create-document/{draft_result['draft_id']}",
                "message": "Great! Let's create your free document."
            }

        except Exception as e:
            logger.error(f"Failed to initiate free document creation: {e}")
            raise

    @staticmethod
    def complete_guest_registration(
        db: Session,
        draft_id: int,
        session_id: str,
        user_data: Dict[str, Any],
        device_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Complete guest registration with enhanced security and user experience"""
        try:
            # Input validation and sanitization
            from app.utils.validation import validate_registration_data
            from app.utils.security import sanitize_user_input
            
            sanitized_data = sanitize_user_input(user_data)
            validation_result = validate_registration_data(sanitized_data)
            
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": "validation_failed",
                    "message": "Invalid registration data",
                    "details": validation_result["errors"]
                }

            # Enhanced security registration with device tracking
            from app.services.auth_service import AuthService
            from app.services.security_monitoring_service import SecurityMonitoringService

            # Monitor for suspicious behavior
            security_check = SecurityMonitoringService.analyze_registration_attempt(
                session_id=session_id,
                email=sanitized_data["email"],
                device_info=device_info
            )

            if not security_check["is_safe"]:
                logger.warning(f"Suspicious registration attempt: {security_check['risk_factors']}")
                return {
                    "success": False,
                    "error": "security_check_failed",
                    "message": "Registration blocked for security reasons",
                    "requires_verification": True
                }

            # Register user with enhanced data
            registration_result = AuthService.register_user(
                db=db,
                email=sanitized_data["email"],
                password=sanitized_data["password"],
                first_name=sanitized_data.get("first_name", ""),
                last_name=sanitized_data.get("last_name", ""),
                phone_number=sanitized_data.get("phone_number"),
                additional_data={
                    "registration_source": "guest_document",
                    "draft_id": draft_id,
                    "device_info": device_info,
                    "utm_data": sanitized_data.get("utm_data"),
                    "referrer": sanitized_data.get("referrer")
                }
            )

            if not registration_result["success"]:
                return registration_result

            user_id = registration_result["user"]["id"]

            # Transfer draft to user
            from app.services.draft_system_service import DocumentDraft

            draft = db.query(DocumentDraft).filter(
                DocumentDraft.id == draft_id,
                DocumentDraft.session_id == session_id
            ).first()

            if draft:
                draft.user_id = user_id
                draft.session_id = None  # Clear session since now belongs to user
                db.commit()

            # Update visit tracking
            visit = db.query(LandingPageVisit).filter(
                LandingPageVisit.session_id == session_id
            ).first()

            if visit:
                visit.registered = True
                visit.converted_at = datetime.utcnow()
                db.commit()

                # Update conversion stats for viewed templates
                if visit.viewed_templates:
                    try:
                        viewed_template_ids = json.loads(visit.viewed_templates)
                        db.query(LandingPageTemplate).filter(
                            LandingPageTemplate.template_id.in_(viewed_template_ids)
                        ).update(
                            {LandingPageTemplate.conversions_count: LandingPageTemplate.conversions_count + 1},
                            synchronize_session=False
                        )
                        db.commit()
                    except:
                        pass

            # Finalize free document for download
            from app.services.draft_system_service import DraftSystemService

            finalize_result = DraftSystemService.finalize_draft_for_payment(
                db=db,
                draft_id=draft_id,
                user_id=user_id
            )

            logger.info(f"Guest registration completed: user {user_id}, draft {draft_id}")

            return {
                "success": True,
                "user_id": user_id,
                "draft_id": draft_id,
                "registration_complete": True,
                "document_ready": finalize_result.get("action") == "free_download",
                "download_url": finalize_result.get("download_url"),
                "access_token": registration_result.get("access_token"),
                "message": "Registration successful! Your document is ready for download.",
                "redirect_to_dashboard": True
            }

        except Exception as e:
            logger.error(f"Failed to complete guest registration: {e}")
            raise

    @staticmethod
    def get_landing_analytics(
        db: Session,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get landing page analytics for admin"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Basic metrics
            total_visits = db.query(LandingPageVisit).filter(
                LandingPageVisit.created_at >= start_date
            ).count()

            conversions = db.query(LandingPageVisit).filter(
                LandingPageVisit.created_at >= start_date,
                LandingPageVisit.registered == True
            ).count()

            document_creations = db.query(LandingPageVisit).filter(
                LandingPageVisit.created_at >= start_date,
                LandingPageVisit.created_document == True
            ).count()

            # Conversion rates
            conversion_rate = (conversions / max(total_visits, 1)) * 100
            document_creation_rate = (document_creations / max(total_visits, 1)) * 100

            # Top performing templates
            top_templates = db.query(
                LandingPageTemplate.template_id,
                LandingPageTemplate.views_count,
                LandingPageTemplate.conversions_count
            ).filter(
                LandingPageTemplate.is_active == True
            ).order_by(
                desc(LandingPageTemplate.conversions_count)
            ).limit(10).all()

            # Traffic sources
            traffic_sources = db.query(
                LandingPageVisit.utm_source,
                func.count(LandingPageVisit.id).label('visits'),
                func.sum(func.cast(LandingPageVisit.registered, Integer)).label('conversions')
            ).filter(
                LandingPageVisit.created_at >= start_date
            ).group_by(
                LandingPageVisit.utm_source
            ).order_by(
                desc('visits')
            ).all()

            return {
                "success": True,
                "period_days": days,
                "metrics": {
                    "total_visits": total_visits,
                    "conversions": conversions,
                    "document_creations": document_creations,
                    "conversion_rate": round(conversion_rate, 2),
                    "document_creation_rate": round(document_creation_rate, 2),
                    "visits_per_day": round(total_visits / max(days, 1), 1)
                },
                "top_templates": [
                    {
                        "template_id": t.template_id,
                        "views": t.views_count,
                        "conversions": t.conversions_count,
                        "conversion_rate": round((t.conversions_count / max(t.views_count, 1)) * 100, 1)
                    } for t in top_templates
                ],
                "traffic_sources": [
                    {
                        "source": t.utm_source or "direct",
                        "visits": t.visits,
                        "conversions": t.conversions or 0,
                        "conversion_rate": round(((t.conversions or 0) / max(t.visits, 1)) * 100, 1)
                    } for t in traffic_sources
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get landing analytics: {e}")
            raise

    @staticmethod
    def _track_search_activity(db: Session, session_id: str, search_term: str):
        """Track search activity for analytics"""
        try:
            visit = db.query(LandingPageVisit).filter(
                LandingPageVisit.session_id == session_id
            ).first()

            if visit:
                # Update search terms
                search_terms = []
                if visit.searched_terms:
                    try:
                        search_terms = json.loads(visit.searched_terms)
                    except:
                        pass

                search_terms.append({
                    "term": search_term,
                    "timestamp": datetime.utcnow().isoformat()
                })

                visit.searched_terms = json.dumps(search_terms[-10:])  # Keep last 10
                visit.searches_performed += 1
                db.commit()

        except Exception as e:
            logger.error(f"Failed to track search activity: {e}")

    @staticmethod
    def _estimate_completion_time(template) -> int:
        """Estimate time to complete document in minutes"""
        # Simple estimation based on template complexity
        base_time = 5  # Base 5 minutes

        # Add time based on name complexity
        if "contract" in template.name.lower():
            return base_time + 10
        elif "invoice" in template.name.lower():
            return base_time + 3
        elif "letter" in template.name.lower():
            return base_time + 2
        else:
            return base_time

    @staticmethod
    def _calculate_relevance(template, search_term: str) -> float:
        """Calculate relevance score for search results"""
        score = 0.0
        term_lower = search_term.lower()

        # Name match (highest weight)
        if term_lower in template.name.lower():
            score += 10.0

        # Description match
        if template.description and term_lower in template.description.lower():
            score += 5.0

        # Category match
        if template.category and term_lower in template.category.lower():
            score += 3.0

        return score

    @staticmethod
    def _get_search_suggestions(db: Session, search_term: str) -> List[str]:
        """Get search suggestions based on popular searches"""
        # Simple implementation - in production, use more sophisticated suggestion engine
        suggestions = [
            "invoice template",
            "business letter",
            "contract agreement",
            "certificate template",
            "resume template",
            "cover letter"
        ]

        # Filter suggestions that contain search term
        relevant_suggestions = [
            s for s in suggestions
            if search_term.lower() not in s.lower() and
            any(word in s.lower() for word in search_term.lower().split())
        ]

        return relevant_suggestions[:5]
