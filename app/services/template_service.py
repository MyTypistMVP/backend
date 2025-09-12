"""
Template management and processing service
"""

import os
import uuid
import hashlib
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from fastapi import UploadFile
from docx import Document as DocxDocument
import redis

from config import settings
from app.models.template import Template, Placeholder
from app.models.user import User
from app.schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateSearch, TemplatePreview,
    TemplateUpload, TemplateRating, TemplateStats, PlaceholderCreate
)
from database import get_db

# Redis client for caching
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)


class TemplateService:
    """Template management and processing service"""

    @staticmethod
    async def create_template(
        db: Session,
        template_data: TemplateCreate,
        file: UploadFile,
        user_id: int,
        preview_file: Optional[UploadFile] = None
    ) -> Template:
        """Create new template with files"""
        try:
            # Generate unique filename
            file_ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            
            # Process main extraction file
            file_path = await process_extraction_file(file, unique_filename)
            file_size = os.path.getsize(file_path)
            file_hash = hashlib.sha256(await file.read()).hexdigest()
            
            # Process preview file if provided, otherwise generate from main file
            preview_file_path = None
            if preview_file:
                preview_filename = f"preview_{unique_filename}"
                preview_file_path = await process_preview_file(preview_file, preview_filename)
            else:
                preview_filename = f"preview_{unique_filename}"
                preview_file_path = await process_preview_file(file, preview_filename)

            # Create template record
            template = Template(
                name=template_data.name,
                description=template_data.description,
                category=template_data.category,
                type=template_data.type,
                language=template_data.language,
                font_family=template_data.font_family,
                font_size=template_data.font_size,
                file_path=file_path,
                preview_file_path=preview_file_path,
                original_filename=file.filename,
                file_size=file_size,
                file_hash=file_hash,
                is_public=template_data.is_public,
                is_premium=template_data.is_premium,
                token_cost=1,  # Default token cost, can be updated later
                price=template_data.price
            )

            db.add(template)
            db.commit()
            db.refresh(template)

            return template

        except Exception as e:
            # Cleanup any created files on error
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            if 'preview_file_path' in locals() and os.path.exists(preview_file_path):
                os.remove(preview_file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create template: {str(e)}"
            )

    @staticmethod
    async def get_template_preview(
        db: Session,
        template_id: int,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get template preview details with analytics tracking"""
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        # Increment preview count
        template.preview_count += 1
        
        # Update preview to download rate
        if template.download_count > 0:
            template.preview_to_download_rate = (
                template.download_count / template.preview_count
            )

        db.commit()

        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "type": template.type,
            "preview_path": template.preview_file_path,
            "is_premium": template.is_premium,
            "token_cost": template.token_cost,
            "rating": template.rating,
            "rating_count": template.rating_count,
            "download_count": template.download_count,
            "average_generation_time": template.average_generation_time
        }

    @staticmethod
    async def update_template_metrics(
        db: Session,
        template_id: int,
        generation_time: Optional[float] = None,
        downloaded: bool = False
    ) -> None:
        """Update template metrics"""
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            return

        if generation_time:
            # Update average generation time
            if template.average_generation_time:
                template.average_generation_time = (
                    template.average_generation_time + generation_time
                ) / 2
            else:
                template.average_generation_time = generation_time

        if downloaded:
            template.download_count += 1
            template.preview_to_download_rate = (
                template.download_count / template.preview_count
                if template.preview_count > 0 else 0
            )

        db.commit()
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from docx import Document as DocxDocument
import redis

from config import settings
from app.models.template import Template, Placeholder
from app.models.template_management import TemplateCategory
from app.models.review import TemplateReview
from app.models.user import User
from app.schemas.template import (
    TemplateCreate,
    TemplateUpdate,
    TemplateSearch,
    TemplatePreview,
    TemplateUpload,
    TemplateRating,
    TemplateStats,
    PlaceholderCreate
)
from app.utils.storage import StorageService
from app.utils.security import validate_file_security
from app.utils.validation import validate_template_metadata
from app.services.audit_service import AuditService
from database import get_db

# Redis client for caching
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

logger = logging.getLogger(__name__)

class TemplateService:
    """Template management and processing service"""
    
    ALLOWED_TEMPLATE_EXTENSIONS = ['.docx', '.pdf', '.txt']
    ALLOWED_PREVIEW_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.pdf']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    # Pricing operations
    PRICE_OPERATIONS = {
        'set': lambda old, new: new,
        'increase': lambda old, new: old + new,
        'decrease': lambda old, new: max(0, old - new),
        'percentage': lambda old, new: old * (1 + new/100)
    }

    @staticmethod
    async def create_template(
        db: Session,
        user_id: int,
        title: str,
        description: str,
        template_file: UploadFile,
        preview_file: UploadFile,
        categories: List[int],
        metadata: Dict[str, Any],
        is_public: bool = True
    ) -> Template:
        """Create a new template"""
        try:
            # Validate files
            await TemplateService._validate_template_files(template_file, preview_file)
            
            # Create template record
            template = Template(
                title=title,
                slug=TemplateService._generate_slug(title),
                description=description,
                created_by=user_id,
                is_public=is_public,
                metadata=metadata,
                approval_status='pending'
            )
            
            # Add categories
            template.categories = (
                db.query(TemplateCategory)
                .filter(TemplateCategory.id.in_(categories))
                .all()
            )
            
            db.add(template)
            db.flush()  # Get template ID
            
            # Store files
            template_path = await StorageService.store_template_file(
                template_file, 
                os.path.join("templates", str(template.id), template_file.filename)
            )
            preview_path = await StorageService.store_preview_file(
                preview_file,
                os.path.join("previews", str(template.id), preview_file.filename)
            )
            
            # Update template with file paths
            template.preview_image_url = preview_path
            template.template_file_url = template_path
            
            db.commit()
            
            # Audit log
            await AuditService.log_action(
                db,
                user_id=user_id,
                action="template_created",
                resource_type="template",
                resource_id=template.id
            )
            
            return template
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create template: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create template: {str(e)}"
            )

    @staticmethod
    async def update_template(
        db: Session,
        template_id: int,
        user_id: int,
        update_data: Dict[str, Any],
        template_file: Optional[UploadFile] = None,
        preview_file: Optional[UploadFile] = None
    ) -> Template:
        """Update template data and files"""
        try:
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template not found"
                )
            
            # Check permissions
            if not await TemplateService._can_edit_template(db, user_id, template):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to edit template"
                )
            
            # Update basic info
            for key, value in update_data.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            # Handle file updates
            if template_file or preview_file:
                # Store new files
                if template_file:
                    template_path = await StorageService.store_template_file(
                        template_file,
                        f"templates/{template.id}/{template_file.filename}"
                    )
                    template.template_file_url = template_path
                
                if preview_file:
                    preview_path = await StorageService.store_preview_file(
                        preview_file,
                        f"previews/{template.id}/{preview_file.filename}"
                    )
                    template.preview_image_url = preview_path
            
            template.updated_at = datetime.utcnow()
            db.commit()
            
            # Audit log
            await AuditService.log_action(
                db,
                user_id=user_id,
                action="template_updated",
                resource_type="template",
                resource_id=template.id
            )
            
            return template
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update template: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update template: {str(e)}"
            )

    @staticmethod
    async def approve_template(
        db: Session,
        template_id: int,
        admin_id: int,
        approval_status: str,
        notes: Optional[str] = None
    ) -> Template:
        """Approve or reject a template"""
        try:
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template not found"
                )
            
            # Verify admin permissions
            admin = db.query(User).filter(User.id == admin_id).first()
            if not admin or not admin.is_admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to approve templates"
                )
            
            template.approval_status = approval_status
            template.approval_notes = notes
            template.approved_by = admin_id
            template.is_approved = (approval_status == 'approved')
            
            db.commit()
            
            # Audit log
            await AuditService.log_action(
                db,
                user_id=admin_id,
                action=f"template_{approval_status}",
                resource_type="template",
                resource_id=template.id,
                metadata={"notes": notes}
            )
            
            return template
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to approve template: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to approve template: {str(e)}"
            )



    @staticmethod
    async def search_templates(
        db: Session,
        search_params: TemplateSearch,
        user_id: Optional[int] = None
    ) -> Tuple[List[Template], int]:
        """Search templates with advanced filters"""
        try:
            query = db.query(Template)

            # Apply search filters
            if search_params.query:
                search = f"%{search_params.query}%"
                query = query.filter(
                    or_(
                        Template.title.ilike(search),
                        Template.description.ilike(search),
                        Template.tags.contains(search)
                    )
                )

            if search_params.categories:
                query = query.filter(Template.categories.any(TemplateCategory.id.in_(search_params.categories)))

            if search_params.is_public is not None:
                query = query.filter(Template.is_public == search_params.is_public)

            if search_params.is_premium is not None:
                query = query.filter(Template.is_premium == search_params.is_premium)

            # Get total count before pagination
            total = query.count()

            # Apply sorting
            if search_params.sort_by:
                if search_params.sort_by == "popular":
                    query = query.order_by(desc(Template.usage_count))
                elif search_params.sort_by == "newest":
                    query = query.order_by(desc(Template.created_at))
                elif search_params.sort_by == "name":
                    query = query.order_by(Template.title)

            # Apply pagination
            query = query.offset(search_params.offset).limit(search_params.limit)

            return query.all(), total

        except Exception as e:
            logger.error(f"Template search failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search templates"
            )

    @staticmethod
    async def get_template_analytics(
        db: Session,
        template_id: int
    ) -> Dict[str, Any]:
        """Get analytics for a template"""
        try:
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template not found"
                )

            # Get usage statistics
            daily_usage = (
                db.query(
                    func.date(Template.created_at).label('date'),
                    func.count().label('count')
                )
                .filter(Template.id == template_id)
                .group_by(func.date(Template.created_at))
                .order_by(func.date(Template.created_at))
                .all()
            )

            return {
                "total_usage": template.usage_count,
                "total_downloads": template.download_count,
                "rating": template.rating,
                "rating_count": template.rating_count,
                "daily_usage": [
                    {
                        "date": str(usage.date),
                        "count": usage.count
                    }
                    for usage in daily_usage
                ]
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get template analytics: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get template analytics"
            )

    # Marketplace features
    @staticmethod
    async def update_template_price(
        db: Session,
        template_id: int,
        new_price: float
    ) -> Template:
        """Update price for a single template"""
        try:
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")

            template.price = new_price
            db.commit()

            return template
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def bulk_update_prices(
        db: Session, 
        filter_type: str, 
        filter_value: Optional[str], 
        price_change: float,
        operation: str
    ) -> int:
        """Update prices in bulk based on filter criteria"""
        if operation not in TemplateService.PRICE_OPERATIONS:
            raise ValueError("Invalid operation")

        # Build query based on filter type
        query = db.query(Template)
        if filter_type == "category":
            query = query.filter(Template.category == filter_value)
        elif filter_type == "tag":
            query = query.filter(Template.tags.contains([filter_value]))
        elif filter_type == "group":
            query = query.filter(Template.type == filter_value)
        elif filter_type != "all":
            raise ValueError("Invalid filter_type")

        operation_func = TemplateService.PRICE_OPERATIONS[operation]
        updated = 0

        try:
            for template in query.all():
                template.price = operation_func(template.price, price_change)
                updated += 1
            db.commit()
            return updated
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def set_special_offer(
        db: Session,
        template_id: int,
        discount_percent: float,
        start_date: datetime,
        end_date: datetime
    ) -> Template:
        """Set a special offer/discount for a template"""
        try:
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")

            template.special_offer = {
                "discount_percent": discount_percent,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "original_price": template.price
            }
            template.price = template.price * (1 - discount_percent/100)
            
            db.commit()
            return template

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    # Private helper methods
    @staticmethod
    async def _calculate_template_hash(template_file: UploadFile) -> str:
        content_hash = await TemplateService._calculate_file_hash(template_file)
        return content_hash

    @staticmethod
    async def _store_preview_file(preview_file: UploadFile, template_id: int) -> str:
        preview_path = await StorageService.store_preview_file(
            preview_file,
            os.path.join("previews", str(template_id), preview_file.filename)
        )
        return preview_path

    @staticmethod

    @staticmethod
    async def _update_template_files(template: Template, template_path: str = None, preview_path: str = None) -> None:
        """Update template file paths"""
        if template_path:
            template.file_path = template_path
        if preview_path:
            template.preview_file_path = preview_path

    @staticmethod
    async def _validate_template_files(
        template_file: UploadFile,
        preview_file: UploadFile
    ) -> None:
        """Validate template and preview files"""
        # Check extensions
        template_ext = os.path.splitext(template_file.filename)[1].lower()
        preview_ext = os.path.splitext(preview_file.filename)[1].lower()
        
        if template_ext not in TemplateService.ALLOWED_TEMPLATE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid template file type. Allowed: {TemplateService.ALLOWED_TEMPLATE_EXTENSIONS}"
            )
        
        if preview_ext not in TemplateService.ALLOWED_PREVIEW_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid preview file type. Allowed: {TemplateService.ALLOWED_PREVIEW_EXTENSIONS}"
            )
        
        # Check file sizes
        template_size = len(await template_file.read())
        preview_size = len(await preview_file.read())
        
        await template_file.seek(0)
        await preview_file.seek(0)
        
        if template_size > TemplateService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template file too large"
            )
        
        if preview_size > TemplateService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Preview file too large"
            )
        
        # Security scan
        await validate_file_security(template_file)
        await validate_file_security(preview_file)

    @staticmethod
    async def _can_edit_template(db: Session, user_id: int, template: Template) -> bool:
        """Check if user can edit template"""
        user = db.query(User).filter(User.id == user_id).first()
        return user and (user.is_admin or template.created_by == user_id)

    @staticmethod
    def _generate_slug(title: str) -> str:
        """Generate URL-friendly slug from title"""
        return "-".join(title.lower().split())

    @staticmethod
    async def _calculate_file_hash(file: UploadFile) -> str:
        """Calculate SHA-256 hash of file contents"""
        hasher = hashlib.sha256()
        content = await file.read()
        hasher.update(content)
        await file.seek(0)
        return hasher.hexdigest()
    
    ALLOWED_TEMPLATE_EXTENSIONS = ['.docx', '.pdf', '.txt']
    ALLOWED_PREVIEW_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.pdf']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    # Pricing operations
    PRICE_OPERATIONS = {
        'set': lambda old, new: new,
        'increase': lambda old, new: old + new,
        'decrease': lambda old, new: max(0, old - new),
        'percentage': lambda old, new: old * (1 + new/100)
    }



    @staticmethod
    def update_template(db: Session, template: Template, template_update: TemplateUpdate) -> Template:
        """Update template"""

        for field, value in template_update.dict(exclude_unset=True).items():
            setattr(template, field, value)

        template.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(template)

        # Update cache
        TemplateService._cache_template(template)

        return template

    @staticmethod
    def delete_template(db: Session, template: Template) -> None:
        """Soft delete template"""

        template.is_active = False
        template.deleted_at = datetime.utcnow()
        db.commit()

        # Remove from cache
        redis_client.delete(f"template:{template.id}")

    @staticmethod
    def search_templates(db: Session, user_id: int, search_params: TemplateSearch) -> Tuple[List[Template], int]:
        """Search templates with advanced filters"""

        query = db.query(Template).filter(Template.is_active == True)

        # Access control - show public templates and user's own templates
        query = query.filter(
            or_(
                Template.is_public == True,
                Template.created_by == user_id
            )
        )

        # Apply filters
        if search_params.query:
            query = query.filter(
                or_(
                    Template.name.contains(search_params.query),
                    Template.description.contains(search_params.query),
                    Template.keywords.contains(search_params.query)
                )
            )

        if search_params.category:
            query = query.filter(Template.category == search_params.category)

        if search_params.type:
            query = query.filter(Template.type == search_params.type)

        if search_params.language:
            query = query.filter(Template.language == search_params.language)

        if search_params.is_public is not None:
            query = query.filter(Template.is_public == search_params.is_public)

        if search_params.is_premium is not None:
            query = query.filter(Template.is_premium == search_params.is_premium)

        if search_params.min_price is not None:
            query = query.filter(Template.price >= search_params.min_price)

        if search_params.max_price is not None:
            query = query.filter(Template.price <= search_params.max_price)

        if search_params.tags:
            # JSON array contains search
            for tag in search_params.tags:
                query = query.filter(Template.tags.contains(f'"{tag}"'))

        # Get total count
        total = query.count()

        # Apply sorting
        if search_params.sort_by == "name":
            order_col = Template.name
        elif search_params.sort_by == "usage_count":
            order_col = Template.usage_count
        elif search_params.sort_by == "rating":
            order_col = Template.rating
        elif search_params.sort_by == "price":
            order_col = Template.price
        else:
            order_col = Template.created_at

        if search_params.sort_order == "asc":
            query = query.order_by(order_col)
        else:
            query = query.order_by(desc(order_col))

        # Apply pagination
        templates = query.offset(
            (search_params.page - 1) * search_params.per_page
        ).limit(search_params.per_page).all()

        return templates, total

    @staticmethod
    def generate_preview(template: Template) -> TemplatePreview:
        """Generate template preview"""

        # Get placeholders
        db = next(get_db())
        placeholders = db.query(Placeholder).filter(
            Placeholder.template_id == template.id
        ).all()
        db.close()

        return TemplatePreview(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            type=template.type,
            placeholders=[
                {
                    "name": ph.name,
                    "display_name": ph.display_name,
                    "type": ph.placeholder_type,
                    "required": ph.is_required
                }
                for ph in placeholders
            ],
            preview_url=f"/api/templates/{template.id}/preview",  # Real preview URL
            watermarked=True
        )

    @staticmethod
    def rate_template(db: Session, template: Template, user_id: int, rating_data: TemplateRating) -> None:
        """Rate a template"""

        # Calculate new rating
        current_total = template.rating * template.rating_count
        new_total = current_total + rating_data.rating
        new_count = template.rating_count + 1
        new_rating = new_total / new_count

        # Update template
        template.rating = round(new_rating, 2)
        template.rating_count = new_count

        db.commit()

        # Store individual rating record for user
        from app.models.template import TemplateRating as TemplateRatingModel

        # Check if user already rated this template
        existing_rating = db.query(TemplateRatingModel).filter(
            TemplateRatingModel.template_id == template.id,
            TemplateRatingModel.user_id == user_id
        ).first()

        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating_data.rating
            existing_rating.comment = rating_data.comment
            existing_rating.updated_at = datetime.utcnow()
        else:
            # Create new rating
            new_rating = TemplateRatingModel(
                template_id=template.id,
                user_id=user_id,
                rating=rating_data.rating,
                comment=rating_data.comment
            )
            db.add(new_rating)

    @staticmethod
    def get_last_used_date(db: Session, template_id: int, user_id: int) -> Optional[datetime]:
        """Get the last used date for a template by a specific user"""

        from app.models.document import Document

        last_document = db.query(Document).filter(
            Document.template_id == template_id,
            Document.user_id == user_id
        ).order_by(desc(Document.created_at)).first()

        return last_document.created_at if last_document else None

    @staticmethod
    def get_template_analytics(db: Session, template_id: int) -> Dict[str, Any]:
        """Get analytics for a template"""

        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            return {}

        # Usage over time (last 30 days)
        from app.models.document import Document
        from datetime import timedelta

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        daily_usage = db.query(
            func.date(Document.created_at).label('date'),
            func.count(Document.id).label('count')
        ).filter(
            Document.template_id == template_id,
            Document.created_at >= thirty_days_ago
        ).group_by(
            func.date(Document.created_at)
        ).all()

        return {
            "template_id": template_id,
            "total_usage": template.usage_count,
            "total_downloads": template.download_count,
            "rating": template.rating,
            "rating_count": template.rating_count,
            "daily_usage": [
                {
                    "date": str(usage.date),
                    "count": usage.count
                }
                for usage in daily_usage
            ]
        }

    @staticmethod
    def _extract_placeholders_from_file(file_path: str) -> List[PlaceholderCreate]:
        """Extract placeholders from document file"""

        placeholders = []
        placeholder_pattern = re.compile(r'\$\{([^}]+)\}')

        try:
            doc = DocxDocument(file_path)

            for p_idx, paragraph in enumerate(doc.paragraphs):
                full_text = ''.join(run.text for run in paragraph.runs)
                matches = placeholder_pattern.finditer(full_text)

                for match in matches:
                    placeholder_name = match.group(1)
                    start_pos = match.start()
                    end_pos = match.end()

                    # Find which runs contain the placeholder
                    current_pos = 0
                    start_run_idx = end_run_idx = None
                    bold = italic = underline = False

                    for r_idx, run in enumerate(paragraph.runs):
                        run_start = current_pos
                        run_end = current_pos + len(run.text)

                        if start_run_idx is None and run_start <= start_pos < run_end:
                            start_run_idx = r_idx
                            bold = run.bold or False
                            italic = run.italic or False
                            underline = run.underline or False

                        if run_start < end_pos <= run_end:
                            end_run_idx = r_idx
                            break

                        current_pos = run_end

                    if start_run_idx is not None and end_run_idx is not None:
                        # Infer placeholder type from name
                        placeholder_type = TemplateService._infer_placeholder_type(placeholder_name)

                        placeholders.append(PlaceholderCreate(
                            name=placeholder_name,
                            display_name=placeholder_name.replace('_', ' ').title(),
                            placeholder_type=placeholder_type,
                            paragraph_index=p_idx,
                            start_run_index=start_run_idx,
                            end_run_index=end_run_idx,
                            bold=bold,
                            italic=italic,
                            underline=underline,
                            is_required=True
                        ))

        except Exception as e:
            print(f"Error extracting placeholders: {e}")

        return placeholders

    @staticmethod
    def _infer_placeholder_type(name: str) -> str:
        """Infer placeholder type from name"""

        name_lower = name.lower()

        if 'date' in name_lower or 'time' in name_lower:
            return 'date'
        elif 'email' in name_lower:
            return 'email'
        elif 'phone' in name_lower or 'tel' in name_lower:
            return 'phone'
        elif 'url' in name_lower or 'website' in name_lower:
            return 'url'
        elif 'amount' in name_lower or 'price' in name_lower or 'cost' in name_lower:
            return 'number'
        else:
            return 'text'

    @staticmethod
    def _detect_document_font(file_path: str) -> Tuple[str, int]:
        """Detect the most common font in document"""

        try:
            doc = DocxDocument(file_path)
            font_counts = {}

            for paragraph in doc.paragraphs:
                for run in paragraph.runs:
                    if run.font.name and run.font.size:
                        key = (run.font.name, int(run.font.size.pt))
                        font_counts[key] = font_counts.get(key, 0) + 1

            if font_counts:
                most_common = max(font_counts.items(), key=lambda x: x[1])
                return most_common[0][0], most_common[0][1]

        except Exception:
            pass

        return "Times New Roman", 12

    @staticmethod
    def _calculate_file_hash(file_path: str) -> str:
        """Calculate SHA256 hash of file"""

        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    @staticmethod
    def _cache_template(template: Template) -> None:
        """Cache template data in Redis"""

        template_data = {
            "id": template.id,
            "name": template.name,
            "category": template.category,
            "type": template.type,
            "file_path": template.file_path,
            "placeholders": template.placeholders,
            "font_family": template.font_family,
            "font_size": template.font_size,
            "is_public": template.is_public,
            "is_premium": template.is_premium,
            "price": template.price
        }

        redis_client.setex(
            f"template:{template.id}",
            settings.TEMPLATE_CACHE_TTL,
            json.dumps(template_data)
        )

    @staticmethod
    def get_cached_template(template_id: int) -> Optional[Dict[str, Any]]:
        """Get template from cache"""

        cached_data = redis_client.get(f"template:{template_id}")
        if cached_data:
            try:
                return json.loads(cached_data)
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def cleanup_unused_templates():
        """Cleanup unused template files (background task)"""

        db = next(get_db())

        try:
            # Get all template files from database
            templates = db.query(Template).filter(Template.is_active == True).all()
            db_file_paths = {template.file_path for template in templates}

            # Get all files in templates directory
            templates_dir = Path(settings.TEMPLATES_PATH)
            if templates_dir.exists():
                for file_path in templates_dir.iterdir():
                    if file_path.is_file() and file_path.name not in db_file_paths:
                        try:
                            file_path.unlink()  # Delete file
                        except OSError:
                            pass

        finally:
            db.close()

    @staticmethod
    def optimize_template_search_index():
        """Optimize template search performance (background task)"""

        db = next(get_db())

        try:
            # Update search vectors for full-text search
            templates = db.query(Template).filter(Template.is_active == True).all()

            for template in templates:
                # Create search vector from name, description, keywords, and tags
                search_terms = []

                if template.name:
                    search_terms.append(template.name.lower())

                if template.description:
                    search_terms.append(template.description.lower())

                if template.keywords:
                    search_terms.append(template.keywords.lower())

                if template.tags:
                    search_terms.extend([tag.lower() for tag in template.tags])

                template.search_vector = " ".join(search_terms)

            db.commit()

        finally:
            db.close()

    @staticmethod
    async def update_template_price(db: Session, template_id: int, new_price: float) -> Template:
        """Update price for a single template"""
        if new_price < 0:
            raise ValueError("Price cannot be negative")
            
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        template.price = new_price
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def bulk_update_prices(
        db: Session, 
        filter_type: str, 
        filter_value: Optional[str], 
        price_change: float,
        operation: str
    ) -> int:
        """Update prices in bulk based on filter criteria"""
        if operation not in ["set", "increase", "decrease", "percentage"]:
            raise ValueError("Invalid operation. Must be: set, increase, decrease, or percentage")

        # Build query based on filter type
        query = db.query(Template)
        if filter_type == "category":
            query = query.filter(Template.category == filter_value)
        elif filter_type == "tag":
            query = query.filter(Template.tags.contains([filter_value]))
        elif filter_type == "group":
            query = query.filter(Template.type == filter_value)
        elif filter_type != "all":
            raise ValueError("Invalid filter_type. Must be: 'all', 'category', 'tag', or 'group'")

        # Update prices using the specified operation
        operations = {
            'set': lambda old, new: new,
            'increase': lambda old, new: old + new,
            'decrease': lambda old, new: max(0, old - new),
            'percentage': lambda old, new: old * (1 + new/100)
        }

        updated_count = 0
        templates = await query.all()
        for template in templates:
            old_price = template.price
            new_price = operations[operation](old_price, price_change)
            if new_price < 0:
                new_price = 0
            
            if new_price != old_price:
                template.price = new_price
                db.add(template)
                updated_count += 1

        if updated_count > 0:
            await db.commit()
        
        return updated_count

    @staticmethod
    async def set_special_offer(
        db: Session,
        template_id: int,
        discount_percent: float,
        start_date: datetime,
        end_date: datetime
    ) -> Template:
        """Set a special offer/discount for a template"""
        if not 0 <= discount_percent <= 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        if end_date <= start_date:
            raise ValueError("End date must be after start date")
            
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise ValueError(f"Template {template_id} not found")
            
        template.special_offer = {
            "discount_percent": discount_percent,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "original_price": template.price
        }
        template.price = template.price * (1 - discount_percent/100)
        
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    def get_popular_templates(db: Session, limit: int = 10) -> List[Template]:
        """Get most popular templates"""

        return db.query(Template).filter(
            Template.is_active == True,
            Template.is_public == True
        ).order_by(
            desc(Template.usage_count)
        ).limit(limit).all()

    @staticmethod
    def get_template_recommendations(db: Session, user_id: int, limit: int = 5) -> List[Template]:
        """Get template recommendations for user"""

        # Simple recommendation based on user's most used categories
        from app.models.document import Document

        user_categories = db.query(
            Template.category,
            func.count(Document.id).label('usage_count')
        ).join(
            Document, Document.template_id == Template.id
        ).filter(
            Document.user_id == user_id
        ).group_by(
            Template.category
        ).order_by(
            desc('usage_count')
        ).limit(3).all()

        if not user_categories:
            # If no usage history, return popular templates
            return TemplateService.get_popular_templates(db, limit)

        # Get templates from user's favorite categories
        categories = [cat.category for cat in user_categories]

        recommended = db.query(Template).filter(
            Template.is_active == True,
            Template.is_public == True,
            Template.category.in_(categories)
        ).order_by(
            desc(Template.rating),
            desc(Template.usage_count)
        ).limit(limit).all()

        return recommended
