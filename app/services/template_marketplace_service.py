"""
Template Marketplace Service
Comprehensive marketplace for template discovery, purchasing, and management
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON, func, desc, and_, or_
from sqlalchemy.orm import relationship
from enum import Enum

from database import Base
from app.models.template import Template
from app.models.user import User
from app.models.payment import Payment
from app.services.audit_service import AuditService
from app.services.payment_service import PaymentService


class MarketplaceCategory(str, Enum):
    """Template marketplace categories"""
    BUSINESS = "business"
    LEGAL = "legal"
    PERSONAL = "personal"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    REAL_ESTATE = "real_estate"
    FINANCE = "finance"
    HR = "human_resources"
    MARKETING = "marketing"
    OTHER = "other"


class TemplateReview(Base):
    """Template reviews and ratings"""
    __tablename__ = "template_reviews"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200), nullable=True)
    comment = Column(Text, nullable=True)

    # Review metadata
    is_verified_purchase = Column(Boolean, nullable=False, default=False)
    helpful_votes = Column(Integer, nullable=False, default=0)
    reported_count = Column(Integer, nullable=False, default=0)
    is_approved = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("Template", backref="reviews")
    user = relationship("User", backref="template_reviews")


class TemplatePurchase(Base):
    """Template purchase history"""
    __tablename__ = "template_purchases"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey('payments.id'), nullable=True, index=True)

    # Purchase details
    amount_paid = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="NGN")
    purchase_type = Column(String(20), nullable=False, default="one_time")  # one_time, subscription

    # Usage tracking
    download_count = Column(Integer, nullable=False, default=0)
    last_downloaded = Column(DateTime, nullable=True)

    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    refunded_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("Template")
    user = relationship("User")
    payment = relationship("Payment")


class TemplateFavorite(Base):
    """User favorite templates"""
    __tablename__ = "template_favorites"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    template = relationship("Template")
    user = relationship("User")


class TemplateCollection(Base):
    """Template collections (curated groups)"""
    __tablename__ = "template_collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)

    # Collection properties
    is_featured = Column(Boolean, nullable=False, default=False)
    is_public = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)

    # Metadata
    template_ids = Column(JSON, nullable=False, default=list)  # List of template IDs
    tags = Column(JSON, nullable=True)

    # Creator
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class TemplateMarketplaceService:
    """Template marketplace management service"""

    @staticmethod
    def get_marketplace_home(db: Session, user_id: Optional[int] = None) -> Dict:
        """Get marketplace homepage data"""

        # Featured templates
        featured_templates = db.query(Template).filter(
            Template.is_active == True,
            Template.is_public == True,
            Template.rating >= 4.0
        ).order_by(desc(Template.usage_count)).limit(8).all()

        # Trending templates (most used in last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        trending_templates = db.query(Template).join(
            TemplatePurchase, Template.id == TemplatePurchase.template_id
        ).filter(
            Template.is_active == True,
            Template.is_public == True,
            TemplatePurchase.created_at >= seven_days_ago
        ).group_by(Template.id).order_by(
            desc(func.count(TemplatePurchase.id))
        ).limit(6).all()

        # New templates
        new_templates = db.query(Template).filter(
            Template.is_active == True,
            Template.is_public == True
        ).order_by(desc(Template.created_at)).limit(6).all()

        # Categories with counts
        category_counts = db.query(
            Template.category,
            func.count(Template.id).label('count')
        ).filter(
            Template.is_active == True,
            Template.is_public == True
        ).group_by(Template.category).all()

        # Featured collections
        featured_collections = db.query(TemplateCollection).filter(
            TemplateCollection.is_featured == True,
            TemplateCollection.is_public == True
        ).order_by(TemplateCollection.sort_order).limit(4).all()

        # User's recent purchases (if logged in)
        recent_purchases = []
        if user_id:
            recent_purchases = db.query(TemplatePurchase).filter(
                TemplatePurchase.user_id == user_id
            ).order_by(desc(TemplatePurchase.created_at)).limit(5).all()

        return {
            "featured_templates": [TemplateMarketplaceService._format_template(t) for t in featured_templates],
            "trending_templates": [TemplateMarketplaceService._format_template(t) for t in trending_templates],
            "new_templates": [TemplateMarketplaceService._format_template(t) for t in new_templates],
            "categories": [{"name": cat[0], "count": cat[1]} for cat in category_counts],
            "featured_collections": [TemplateMarketplaceService._format_collection(c) for c in featured_collections],
            "recent_purchases": [TemplateMarketplaceService._format_purchase(p) for p in recent_purchases]
        }

    @staticmethod
    def search_marketplace(db: Session, query: str = None, category: str = None,
                          min_price: float = None, max_price: float = None,
                          rating: float = None, sort_by: str = "relevance",
                          page: int = 1, per_page: int = 20, user_id: Optional[int] = None) -> Dict:
        """Advanced marketplace search"""

        # Base query
        base_query = db.query(Template).filter(
            Template.is_active == True,
            Template.is_public == True
        )

        # Text search
        if query:
            base_query = base_query.filter(
                or_(
                    Template.name.ilike(f"%{query}%"),
                    Template.description.ilike(f"%{query}%"),
                    Template.keywords.ilike(f"%{query}%"),
                    Template.tags.contains(f'"{query}"')
                )
            )

        # Category filter
        if category:
            base_query = base_query.filter(Template.category == category)

        # Price filters
        if min_price is not None:
            base_query = base_query.filter(Template.price >= min_price)
        if max_price is not None:
            base_query = base_query.filter(Template.price <= max_price)

        # Rating filter
        if rating:
            base_query = base_query.filter(Template.rating >= rating)

        # Sorting
        if sort_by == "price_low":
            base_query = base_query.order_by(Template.price)
        elif sort_by == "price_high":
            base_query = base_query.order_by(desc(Template.price))
        elif sort_by == "rating":
            base_query = base_query.order_by(desc(Template.rating))
        elif sort_by == "popularity":
            base_query = base_query.order_by(desc(Template.usage_count))
        elif sort_by == "newest":
            base_query = base_query.order_by(desc(Template.created_at))
        else:  # relevance (default)
            if query:
                # Boost exact matches
                base_query = base_query.order_by(
                    Template.name.ilike(f"%{query}%").desc(),
                    desc(Template.rating),
                    desc(Template.usage_count)
                )
            else:
                base_query = base_query.order_by(desc(Template.rating), desc(Template.usage_count))

        # Get total count
        total = base_query.count()

        # Apply pagination
        templates = base_query.offset((page - 1) * per_page).limit(per_page).all()

        # Get user's purchased templates (if logged in)
        purchased_template_ids = set()
        if user_id:
            purchases = db.query(TemplatePurchase.template_id).filter(
                TemplatePurchase.user_id == user_id,
                TemplatePurchase.is_active == True
            ).all()
            purchased_template_ids = {p[0] for p in purchases}

        return {
            "templates": [
                {
                    **TemplateMarketplaceService._format_template(t),
                    "is_purchased": t.id in purchased_template_ids
                }
                for t in templates
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
            "filters": {
                "query": query,
                "category": category,
                "min_price": min_price,
                "max_price": max_price,
                "rating": rating,
                "sort_by": sort_by
            }
        }

    @staticmethod
    def get_template_details(db: Session, template_id: int, user_id: Optional[int] = None) -> Dict:
        """Get detailed template information"""

        template = db.query(Template).filter(
            Template.id == template_id,
            Template.is_active == True
        ).first()

        if not template:
            return None

        # Check if user has purchased
        is_purchased = False
        purchase_date = None
        if user_id:
            purchase = db.query(TemplatePurchase).filter(
                TemplatePurchase.template_id == template_id,
                TemplatePurchase.user_id == user_id,
                TemplatePurchase.is_active == True
            ).first()
            if purchase:
                is_purchased = True
                purchase_date = purchase.created_at

        # Get reviews
        reviews = db.query(TemplateReview).filter(
            TemplateReview.template_id == template_id,
            TemplateReview.is_approved == True
        ).order_by(desc(TemplateReview.created_at)).limit(10).all()

        # Get related templates
        related_templates = db.query(Template).filter(
            Template.category == template.category,
            Template.id != template_id,
            Template.is_active == True,
            Template.is_public == True
        ).order_by(desc(Template.rating)).limit(4).all()

        # Check if user has favorited
        is_favorited = False
        if user_id:
            favorite = db.query(TemplateFavorite).filter(
                TemplateFavorite.template_id == template_id,
                TemplateFavorite.user_id == user_id
            ).first()
            is_favorited = bool(favorite)

        return {
            **TemplateMarketplaceService._format_template(template),
            "is_purchased": is_purchased,
            "purchase_date": purchase_date,
            "is_favorited": is_favorited,
            "reviews": [TemplateMarketplaceService._format_review(r) for r in reviews],
            "related_templates": [TemplateMarketplaceService._format_template(t) for t in related_templates],
            "placeholders": template.placeholders or [],
            "preview_available": bool(template.file_path)
        }

    @staticmethod
    def purchase_template(db: Session, template_id: int, user_id: int, payment_method: str = "wallet") -> Dict:
        """Purchase a template"""

        template = db.query(Template).filter(
            Template.id == template_id,
            Template.is_active == True,
            Template.is_public == True
        ).first()

        if not template:
            return {"success": False, "error": "Template not found"}

        # Check if already purchased
        existing_purchase = db.query(TemplatePurchase).filter(
            TemplatePurchase.template_id == template_id,
            TemplatePurchase.user_id == user_id,
            TemplatePurchase.is_active == True
        ).first()

        if existing_purchase:
            return {"success": False, "error": "Template already purchased"}

        # Free template
        if template.price == 0:
            purchase = TemplatePurchase(
                template_id=template_id,
                user_id=user_id,
                amount_paid=0,
                currency="NGN"
            )
            db.add(purchase)
            db.commit()

            # Update template stats
            template.usage_count += 1
            template.download_count += 1
            db.commit()

            return {"success": True, "purchase_id": purchase.id, "amount": 0}

        # Paid template - integrate with payment service
        try:
            payment_result = PaymentService.process_template_purchase(
                db, user_id, template_id, template.price, payment_method
            )

            if payment_result["success"]:
                purchase = TemplatePurchase(
                    template_id=template_id,
                    user_id=user_id,
                    payment_id=payment_result["payment_id"],
                    amount_paid=template.price,
                    currency="NGN"
                )
                db.add(purchase)
                db.commit()

                # Update template stats
                template.usage_count += 1
                template.download_count += 1
                db.commit()

                # Log purchase
                AuditService.log_system_event(
                    "TEMPLATE_PURCHASED",
                    {
                        "template_id": template_id,
                        "user_id": user_id,
                        "amount": template.price,
                        "purchase_id": purchase.id
                    }
                )

                return {
                    "success": True,
                    "purchase_id": purchase.id,
                    "amount": template.price,
                    "payment_id": payment_result["payment_id"]
                }
            else:
                return {"success": False, "error": payment_result["error"]}

        except Exception as e:
            return {"success": False, "error": f"Payment processing failed: {str(e)}"}

    @staticmethod
    def add_template_review(db: Session, template_id: int, user_id: int, rating: int,
                           title: str = None, comment: str = None) -> Dict:
        """Add a review for a template"""

        # Validate rating
        if not (1 <= rating <= 5):
            return {"success": False, "error": "Rating must be between 1 and 5"}

        # Check if user has purchased the template
        purchase = db.query(TemplatePurchase).filter(
            TemplatePurchase.template_id == template_id,
            TemplatePurchase.user_id == user_id,
            TemplatePurchase.is_active == True
        ).first()

        is_verified_purchase = bool(purchase)

        # Check if user already reviewed
        existing_review = db.query(TemplateReview).filter(
            TemplateReview.template_id == template_id,
            TemplateReview.user_id == user_id
        ).first()

        if existing_review:
            # Update existing review
            existing_review.rating = rating
            existing_review.title = title
            existing_review.comment = comment
            existing_review.updated_at = datetime.utcnow()
            db.commit()
            review_id = existing_review.id
        else:
            # Create new review
            review = TemplateReview(
                template_id=template_id,
                user_id=user_id,
                rating=rating,
                title=title,
                comment=comment,
                is_verified_purchase=is_verified_purchase
            )
            db.add(review)
            db.commit()
            review_id = review.id

        # Update template rating
        TemplateMarketplaceService._update_template_rating(db, template_id)

        return {"success": True, "review_id": review_id}

    @staticmethod
    def toggle_favorite(db: Session, template_id: int, user_id: int) -> Dict:
        """Toggle template favorite status"""

        existing_favorite = db.query(TemplateFavorite).filter(
            TemplateFavorite.template_id == template_id,
            TemplateFavorite.user_id == user_id
        ).first()

        if existing_favorite:
            # Remove favorite
            db.delete(existing_favorite)
            db.commit()
            return {"success": True, "is_favorited": False}
        else:
            # Add favorite
            favorite = TemplateFavorite(
                template_id=template_id,
                user_id=user_id
            )
            db.add(favorite)
            db.commit()
            return {"success": True, "is_favorited": True}

    @staticmethod
    def get_user_purchases(db: Session, user_id: int, page: int = 1, per_page: int = 20) -> Dict:
        """Get user's template purchases"""

        query = db.query(TemplatePurchase).filter(
            TemplatePurchase.user_id == user_id,
            TemplatePurchase.is_active == True
        ).order_by(desc(TemplatePurchase.created_at))

        total = query.count()
        purchases = query.offset((page - 1) * per_page).limit(per_page).all()

        return {
            "purchases": [TemplateMarketplaceService._format_purchase(p) for p in purchases],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    @staticmethod
    def get_user_favorites(db: Session, user_id: int, page: int = 1, per_page: int = 20) -> Dict:
        """Get user's favorite templates"""

        query = db.query(TemplateFavorite).filter(
            TemplateFavorite.user_id == user_id
        ).order_by(desc(TemplateFavorite.created_at))

        total = query.count()
        favorites = query.offset((page - 1) * per_page).limit(per_page).all()

        return {
            "favorites": [
                {
                    "favorited_at": fav.created_at,
                    "template": TemplateMarketplaceService._format_template(fav.template)
                }
                for fav in favorites
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    @staticmethod
    def _format_template(template: Template) -> Dict:
        """Format template for API response"""
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "type": template.type,
            "price": template.price,
            "is_premium": template.is_premium,
            "rating": template.rating,
            "rating_count": template.rating_count,
            "usage_count": template.usage_count,
            "download_count": template.download_count,
            "tags": template.tags or [],
            "language": template.language,
            "created_at": template.created_at,
            "preview_url": f"/api/templates/{template.id}/preview" if template.file_path else None
        }

    @staticmethod
    def _format_review(review: TemplateReview) -> Dict:
        """Format review for API response"""
        return {
            "id": review.id,
            "rating": review.rating,
            "title": review.title,
            "comment": review.comment,
            "is_verified_purchase": review.is_verified_purchase,
            "helpful_votes": review.helpful_votes,
            "created_at": review.created_at,
            "user": {
                "id": review.user.id,
                "name": review.user.full_name,
                "avatar": f"/api/users/{template.created_by}/avatar"  # Real user avatar URL
            }
        }

    @staticmethod
    def _format_purchase(purchase: TemplatePurchase) -> Dict:
        """Format purchase for API response"""
        return {
            "id": purchase.id,
            "amount_paid": purchase.amount_paid,
            "currency": purchase.currency,
            "download_count": purchase.download_count,
            "last_downloaded": purchase.last_downloaded,
            "created_at": purchase.created_at,
            "template": TemplateMarketplaceService._format_template(purchase.template)
        }

    @staticmethod
    def _format_collection(collection: TemplateCollection) -> Dict:
        """Format collection for API response"""
        return {
            "id": collection.id,
            "name": collection.name,
            "description": collection.description,
            "slug": collection.slug,
            "is_featured": collection.is_featured,
            "template_count": len(collection.template_ids),
            "created_at": collection.created_at
        }

    @staticmethod
    def _update_template_rating(db: Session, template_id: int):
        """Recalculate template rating based on reviews"""

        reviews = db.query(TemplateReview).filter(
            TemplateReview.template_id == template_id,
            TemplateReview.is_approved == True
        ).all()

        if reviews:
            total_rating = sum(review.rating for review in reviews)
            avg_rating = total_rating / len(reviews)

            template = db.query(Template).filter(Template.id == template_id).first()
            if template:
                template.rating = round(avg_rating, 2)
                template.rating_count = len(reviews)
                db.commit()

    @staticmethod
    def get_marketplace_stats(db: Session) -> Dict:
        """Get marketplace statistics"""

        total_templates = db.query(Template).filter(
            Template.is_active == True,
            Template.is_public == True
        ).count()

        free_templates = db.query(Template).filter(
            Template.is_active == True,
            Template.is_public == True,
            Template.price == 0
        ).count()

        premium_templates = total_templates - free_templates

        total_purchases = db.query(TemplatePurchase).filter(
            TemplatePurchase.is_active == True
        ).count()

        total_revenue = db.query(func.sum(TemplatePurchase.amount_paid)).filter(
            TemplatePurchase.is_active == True
        ).scalar() or 0

        total_reviews = db.query(TemplateReview).filter(
            TemplateReview.is_approved == True
        ).count()

        avg_rating = db.query(func.avg(TemplateReview.rating)).filter(
            TemplateReview.is_approved == True
        ).scalar() or 0

        return {
            "total_templates": total_templates,
            "free_templates": free_templates,
            "premium_templates": premium_templates,
            "total_purchases": total_purchases,
            "total_revenue": round(total_revenue, 2),
            "total_reviews": total_reviews,
            "average_rating": round(avg_rating, 2) if avg_rating else 0
        }
