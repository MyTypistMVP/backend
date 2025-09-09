"""
Document Version Control Routes
Track changes, view history, and restore previous versions
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from app.models.user import User
from app.services.document_version_service import DocumentVersionService
from app.services.audit_service import AuditService
from app.utils.security import get_current_active_user

router = APIRouter()


class CreateVersionRequest(BaseModel):
    """Request model for creating document version"""
    document_id: int
    title: str
    content: Optional[str] = None
    placeholder_data: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    change_summary: Optional[str] = None
    change_type: str = "edit"
    generation_time: Optional[int] = None


class RestoreVersionRequest(BaseModel):
    """Request model for restoring document version"""
    restore_reason: Optional[str] = None


@router.post("/create", response_model=Dict[str, Any])
async def create_document_version(
    version_request: CreateVersionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new version of a document"""
    try:
        # Verify user owns the document or is admin
        from app.models.document import Document
        document = db.query(Document).filter(
            Document.id == version_request.document_id
        ).first()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        if document.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to modify this document"
            )

        # Create version
        result = DocumentVersionService.create_version(
            db=db,
            document_id=version_request.document_id,
            user_id=current_user.id,
            title=version_request.title,
            content=version_request.content,
            placeholder_data=version_request.placeholder_data,
            file_path=version_request.file_path,
            file_size=version_request.file_size,
            change_summary=version_request.change_summary,
            change_type=version_request.change_type,
            generation_time=version_request.generation_time
        )

        # Log the version creation
        AuditService.log_user_activity(
            db,
            current_user.id,
            "DOCUMENT_VERSION_CREATED",
            {
                "document_id": version_request.document_id,
                "version_number": result["version_number"],
                "change_type": version_request.change_type,
                "generation_time": version_request.generation_time
            }
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document version: {str(e)}"
        )


@router.get("/document/{document_id}/history", response_model=Dict[str, Any])
async def get_document_version_history(
    document_id: int,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get version history for a document"""
    try:
        result = DocumentVersionService.get_document_versions(
            db=db,
            document_id=document_id,
            user_id=current_user.id,
            limit=limit
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document history: {str(e)}"
        )


@router.get("/version/{version_id}", response_model=Dict[str, Any])
async def get_version_details(
    version_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific version"""
    try:
        result = DocumentVersionService.get_version_details(
            db=db,
            version_id=version_id,
            user_id=current_user.id
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get version details: {str(e)}"
        )


@router.post("/version/{version_id}/restore", response_model=Dict[str, Any])
async def restore_document_version(
    version_id: int,
    restore_request: RestoreVersionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Restore a previous version as the current version"""
    try:
        result = DocumentVersionService.restore_version(
            db=db,
            version_id=version_id,
            user_id=current_user.id,
            restore_reason=restore_request.restore_reason
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=result["error"]
            )

        # Log the version restoration
        AuditService.log_user_activity(
            db,
            current_user.id,
            "DOCUMENT_VERSION_RESTORED",
            {
                "document_id": result["document_id"],
                "restored_from_version": result["restored_from_version"],
                "new_version": result["new_version"],
                "restore_reason": restore_request.restore_reason
            }
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore version: {str(e)}"
        )


@router.get("/compare/{version_id_1}/{version_id_2}", response_model=Dict[str, Any])
async def compare_document_versions(
    version_id_1: int,
    version_id_2: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Compare two document versions"""
    try:
        result = DocumentVersionService.compare_versions(
            db=db,
            version_id_1=version_id_1,
            version_id_2=version_id_2,
            user_id=current_user.id
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare versions: {str(e)}"
        )


@router.get("/user/time-savings", response_model=Dict[str, Any])
async def get_user_time_savings(
    days: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user's time savings statistics
    Shows how much time the user has saved using the platform vs manual document creation
    """
    try:
        result = DocumentVersionService.get_user_time_savings(
            db=db,
            user_id=current_user.id,
            days=days
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time savings: {str(e)}"
        )


@router.get("/performance/generation-times", response_model=Dict[str, Any])
async def get_document_generation_performance(
    days: int = 7,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get document generation performance statistics
    Shows generation times and performance trends
    """
    try:
        from datetime import datetime, timedelta
        from app.services.document_version_service import DocumentVersion

        start_date = datetime.utcnow() - timedelta(days=days)

        # Get recent versions with generation times
        versions = db.query(DocumentVersion).filter(
            DocumentVersion.changed_by == current_user.id,
            DocumentVersion.created_at >= start_date,
            DocumentVersion.generation_time.isnot(None)
        ).order_by(DocumentVersion.created_at.desc()).all()

        if not versions:
            return {
                "success": True,
                "message": "No generation data available for the specified period",
                "statistics": {
                    "total_documents": 0,
                    "average_generation_time": 0,
                    "fastest_generation": 0,
                    "slowest_generation": 0,
                    "performance_trend": "stable"
                }
            }

        generation_times = [v.generation_time for v in versions]
        avg_time = sum(generation_times) / len(generation_times)

        # Performance trend calculation (simple)
        if len(generation_times) >= 5:
            recent_avg = sum(generation_times[:5]) / 5
            older_avg = sum(generation_times[-5:]) / 5

            if recent_avg < older_avg * 0.9:
                trend = "improving"
            elif recent_avg > older_avg * 1.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "success": True,
            "period_days": days,
            "statistics": {
                "total_documents": len(versions),
                "average_generation_time_ms": round(avg_time, 2),
                "average_generation_time_seconds": round(avg_time / 1000, 2),
                "fastest_generation_ms": min(generation_times),
                "slowest_generation_ms": max(generation_times),
                "performance_trend": trend,
                "documents_per_day": round(len(versions) / days, 2)
            },
            "recent_generations": [
                {
                    "document_id": v.document_id,
                    "generation_time_ms": v.generation_time,
                    "generation_time_seconds": round(v.generation_time / 1000, 2),
                    "created_at": v.created_at.isoformat(),
                    "estimated_time_saved": v.estimated_time_saved
                }
                for v in versions[:10]  # Last 10 generations
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get generation performance: {str(e)}"
        )
