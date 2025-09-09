"""
Document Sharing Routes
Time-limited preview links with password protection and view tracking
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, validator

from database import get_db
from app.models.user import User
from app.services.admin_dashboard_service import AdminDashboardService
from app.services.audit_service import AuditService
from app.utils.security import get_current_active_user

router = APIRouter()


class DocumentShareRequest(BaseModel):
    """Request model for creating document share"""
    document_id: int
    hours_valid: int = 5
    max_views: Optional[int] = None

    @validator('hours_valid')
    def validate_hours(cls, v):
        if v < 1 or v > 168:  # Max 1 week
            raise ValueError('Hours valid must be between 1 and 168 (1 week)')
        return v

    @validator('max_views')
    def validate_max_views(cls, v):
        if v is not None and (v < 1 or v > 1000):
            raise ValueError('Max views must be between 1 and 1000')
        return v


class DocumentShareAccessRequest(BaseModel):
    """Request model for accessing shared document"""
    password: str


@router.post("/create", response_model=Dict[str, Any])
async def create_document_share(
    share_request: DocumentShareRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a time-limited shareable link for document preview
    Users can share their documents with others for review/feedback
    """
    try:
        # Verify user owns the document or has permission
        from app.models.document import Document
        document = db.query(Document).filter(
            Document.id == share_request.document_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Check ownership or admin permission
        if document.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to share this document"
            )

        # Create the share
        result = AdminDashboardService.create_document_share(
            db=db,
            document_id=share_request.document_id,
            shared_by=current_user.id,
            hours_valid=share_request.hours_valid,
            max_views=share_request.max_views
        )

        # Log the sharing activity
        AuditService.log_user_activity(
            db,
            current_user.id,
            "DOCUMENT_SHARED",
            {
                "document_id": share_request.document_id,
                "share_token": result["share_token"],
                "hours_valid": share_request.hours_valid,
                "max_views": share_request.max_views
            }
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document share: {str(e)}"
        )


@router.get("/shared/{share_token}", response_model=Dict[str, Any])
async def get_shared_document_info(
    share_token: str,
    db: Session = Depends(get_db)
):
    """
    Get information about a shared document (without accessing it)
    Shows expiration time, view limits, etc.
    """
    try:
        from app.services.admin_dashboard_service import DocumentShare

        share = db.query(DocumentShare).filter(
            DocumentShare.share_token == share_token,
            DocumentShare.is_active == True
        ).first()

        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share link not found or expired"
            )

        # Check if expired
        from datetime import datetime
        if datetime.utcnow() > share.expires_at:
            share.is_active = False
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Share link has expired"
            )

        # Get document title (without content)
        from app.models.document import Document
        document = db.query(Document).filter(
            Document.id == share.document_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        return {
            "success": True,
            "share_token": share_token,
            "document_title": document.title,
            "expires_at": share.expires_at.isoformat(),
            "requires_password": bool(share.share_password),
            "max_views": share.max_views,
            "current_views": share.current_views,
            "views_remaining": (share.max_views - share.current_views) if share.max_views else None,
            "created_at": share.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get shared document info: {str(e)}"
        )


@router.post("/shared/{share_token}/access", response_model=Dict[str, Any])
async def access_shared_document(
    share_token: str,
    access_request: DocumentShareAccessRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Access a shared document with password
    Provides view-only access to the document content
    """
    try:
        # Get client IP for logging
        client_ip = request.client.host if request.client else None

        # Access the document
        result = AdminDashboardService.access_shared_document(
            db=db,
            share_token=share_token,
            password=access_request.password,
            ip_address=client_ip
        )

        # Track the page visit for analytics
        if result["success"]:
            AdminDashboardService.track_page_visit(
                db=db,
                page_path=f"/shared/{share_token}",
                session_id=f"share_{share_token}",
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to access shared document: {str(e)}"
        )


@router.get("/my-shares", response_model=Dict[str, Any])
async def get_my_document_shares(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all document shares created by the current user
    """
    try:
        from app.services.admin_dashboard_service import DocumentShare
        from app.models.document import Document

        shares = db.query(DocumentShare).filter(
            DocumentShare.shared_by == current_user.id
        ).order_by(DocumentShare.created_at.desc()).all()

        share_data = []
        for share in shares:
            # Get document info
            document = db.query(Document).filter(
                Document.id == share.document_id
            ).first()

            share_data.append({
                "share_id": share.id,
                "share_token": share.share_token,
                "document_id": share.document_id,
                "document_title": document.title if document else "Unknown",
                "expires_at": share.expires_at.isoformat(),
                "is_active": share.is_active,
                "max_views": share.max_views,
                "current_views": share.current_views,
                "created_at": share.created_at.isoformat(),
                "last_accessed": share.last_accessed.isoformat() if share.last_accessed else None,
                "share_url": f"/shared/{share.share_token}"
            })

        return {
            "success": True,
            "shares": share_data,
            "total_shares": len(share_data)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document shares: {str(e)}"
        )


@router.delete("/shared/{share_token}")
async def deactivate_document_share(
    share_token: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a document share (revoke access)
    """
    try:
        from app.services.admin_dashboard_service import DocumentShare

        share = db.query(DocumentShare).filter(
            DocumentShare.share_token == share_token
        ).first()

        if not share:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share not found"
            )

        # Check ownership or admin permission
        if share.shared_by != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to deactivate this share"
            )

        # Deactivate the share
        share.is_active = False
        db.commit()

        # Log the action
        AuditService.log_user_activity(
            db,
            current_user.id,
            "DOCUMENT_SHARE_DEACTIVATED",
            {
                "share_token": share_token,
                "document_id": share.document_id
            }
        )

        return {
            "success": True,
            "message": "Document share has been deactivated"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate document share: {str(e)}"
        )


@router.get("/admin/shares", response_model=Dict[str, Any])
async def get_all_document_shares(
    page: int = 1,
    limit: int = 50,
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to view all document shares
    """
    try:
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )

        from app.services.admin_dashboard_service import DocumentShare
        from app.models.document import Document

        query = db.query(DocumentShare)

        if active_only:
            query = query.filter(DocumentShare.is_active == True)

        # Get total count
        total_shares = query.count()

        # Apply pagination
        offset = (page - 1) * limit
        shares = query.order_by(DocumentShare.created_at.desc()).offset(offset).limit(limit).all()

        share_data = []
        for share in shares:
            # Get document and user info
            document = db.query(Document).filter(
                Document.id == share.document_id
            ).first()

            user = db.query(User).filter(
                User.id == share.shared_by
            ).first()

            share_data.append({
                "share_id": share.id,
                "share_token": share.share_token,
                "document_id": share.document_id,
                "document_title": document.title if document else "Unknown",
                "shared_by": {
                    "id": user.id if user else None,
                    "email": user.email if user else "Unknown"
                },
                "expires_at": share.expires_at.isoformat(),
                "is_active": share.is_active,
                "max_views": share.max_views,
                "current_views": share.current_views,
                "created_at": share.created_at.isoformat(),
                "last_accessed": share.last_accessed.isoformat() if share.last_accessed else None
            })

        return {
            "success": True,
            "shares": share_data,
            "pagination": {
                "total": total_shares,
                "page": page,
                "limit": limit,
                "total_pages": (total_shares + limit - 1) // limit
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document shares: {str(e)}"
        )
