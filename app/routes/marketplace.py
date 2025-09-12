"""
Template Marketplace Routes
API endpoints for template marketplace functionality
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from database import get_db
from app.models.user import User
from app.utils.security import get_current_active_user
from app.services.template_service import TemplateService
from app.services.audit_service import AuditService

router = APIRouter()


@router.get("/home")
async def get_marketplace_home(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get marketplace homepage data"""

    homepage_data = TemplateMarketplaceService.get_marketplace_home(db, current_user.id)
    return homepage_data


@router.get("/search")
async def search_marketplace(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    rating: Optional[float] = Query(None, ge=1, le=5, description="Minimum rating filter"),
    sort_by: str = Query("relevance", description="Sort by: relevance, price_low, price_high, rating, popularity, newest"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Search templates in marketplace"""

    search_results = TemplateMarketplaceService.search_marketplace(
        db, query, category, min_price, max_price, rating, sort_by, page, per_page, current_user.id
    )

    return search_results


@router.get("/templates/{template_id}")
async def get_template_details(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed template information"""

    template_details = TemplateMarketplaceService.get_template_details(db, template_id, current_user.id)

    if not template_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return template_details


@router.post("/templates/{template_id}/purchase")
async def purchase_template(
    template_id: int,
    payment_method: str = "wallet",
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Purchase a template"""

    purchase_result = TemplateMarketplaceService.purchase_template(
        db, template_id, current_user.id, payment_method
    )

    if not purchase_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=purchase_result["error"]
        )

    # Log purchase
    AuditService.log_system_event(
        "TEMPLATE_PURCHASED",
        {
            "user_id": current_user.id,
            "template_id": template_id,
            "purchase_id": purchase_result["purchase_id"],
            "amount": purchase_result["amount"]
        }
    )

    return purchase_result


@router.post("/templates/{template_id}/review")
async def add_template_review(
    template_id: int,
    rating: int = Query(..., ge=1, le=5, description="Rating from 1 to 5 stars"),
    title: Optional[str] = Query(None, max_length=200, description="Review title"),
    comment: Optional[str] = Query(None, max_length=1000, description="Review comment"),
    request: Request = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add or update template review"""

    review_result = TemplateMarketplaceService.add_template_review(
        db, template_id, current_user.id, rating, title, comment
    )

    if not review_result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=review_result["error"]
        )

    # Log review
    AuditService.log_system_event(
        "TEMPLATE_REVIEWED",
        {
            "user_id": current_user.id,
            "template_id": template_id,
            "review_id": review_result["review_id"],
            "rating": rating
        }
    )

    return {"message": "Review added successfully", "review_id": review_result["review_id"]}


@router.post("/templates/{template_id}/favorite")
async def toggle_template_favorite(
    template_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Toggle template favorite status"""

    result = TemplateMarketplaceService.toggle_favorite(db, template_id, current_user.id)

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to toggle favorite"
        )

    action = "added to" if result["is_favorited"] else "removed from"
    return {"message": f"Template {action} favorites", "is_favorited": result["is_favorited"]}


@router.get("/my/purchases")
async def get_my_purchases(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's template purchases"""

    purchases = TemplateMarketplaceService.get_user_purchases(db, current_user.id, page, per_page)
    return purchases


@router.get("/my/favorites")
async def get_my_favorites(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's favorite templates"""

    favorites = TemplateMarketplaceService.get_user_favorites(db, current_user.id, page, per_page)
    return favorites


@router.get("/stats")
async def get_marketplace_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get marketplace statistics"""

    stats = TemplateMarketplaceService.get_marketplace_stats(db)
    return stats
