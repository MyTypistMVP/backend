"""
Template Management Service
Handles template upload, metadata, versioning, and management operations
"""

import os
import json
import hashlib
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.template_management import Template, TemplateVersion, TemplateCategory, TemplateReview
from app.models.user import User
from app.utils.storage import StorageService
from app.utils.security import validate_file_security
from app.utils.validation import validate_template_metadata
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

class TemplateManagementService:
    """Service for managing templates and their versions"""
    
    ALLOWED_TEMPLATE_EXTENSIONS = ['.docx', '.pdf', '.txt']
    ALLOWED_PREVIEW_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.pdf']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
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
        """Create a new template with initial version"""
        try:
            # Validate files
            await TemplateManagementService._validate_template_files(template_file, preview_file)
            
            # Create template record
            template = Template(
                title=title,
                slug=TemplateManagementService._generate_slug(title),
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
                f"templates/{template.id}/v1/{template_file.filename}"
            )
            preview_path = await StorageService.store_preview_file(
                preview_file,
                f"previews/{template.id}/v1/{preview_file.filename}"
            )
            
            # Create initial version
            version = TemplateVersion(
                template_id=template.id,
                version_number="1.0.0",
                content_hash=await TemplateManagementService._calculate_file_hash(template_file),
                template_file_path=template_path,
                preview_file_path=preview_path,
                created_by=user_id,
                changes=["Initial version"],
                metadata=metadata
            )
            
            # Update template with version info
            template.current_version = "1.0.0"
            template.first_version = "1.0.0"
            template.latest_version = "1.0.0"
            template.preview_image_url = preview_path
            template.template_file_url = template_path
            
            db.add(version)
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
        """Update template and create new version if files changed"""
        try:
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Template not found"
                )
            
            # Check permissions
            if not await TemplateManagementService._can_edit_template(db, user_id, template):
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
                await TemplateManagementService._create_new_version(
                    db, template, user_id, template_file, preview_file, update_data.get("changes", [])
                )
            
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
    async def get_template_versions(
        db: Session,
        template_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[TemplateVersion]:
        """Get version history for a template"""
        try:
            versions = (
                db.query(TemplateVersion)
                .filter(TemplateVersion.template_id == template_id)
                .order_by(desc(TemplateVersion.created_at))
                .offset(offset)
                .limit(limit)
                .all()
            )
            return versions
            
        except Exception as e:
            logger.error(f"Failed to get template versions: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get template versions"
            )
    
    @staticmethod
    async def _create_new_version(
        db: Session,
        template: Template,
        user_id: int,
        template_file: Optional[UploadFile],
        preview_file: Optional[UploadFile],
        changes: List[str]
    ) -> TemplateVersion:
        """Create a new version of a template"""
        try:
            # Validate files if provided
            if template_file and preview_file:
                await TemplateManagementService._validate_template_files(template_file, preview_file)
            
            # Generate new version number
            current_version = template.latest_version
            new_version = TemplateManagementService._increment_version(current_version)
            
            # Store new files
            template_path = None
            preview_path = None
            content_hash = None
            
            if template_file:
                template_path = await StorageService.store_template_file(
                    template_file,
                    f"templates/{template.id}/v{new_version}/{template_file.filename}"
                )
                content_hash = await TemplateManagementService._calculate_file_hash(template_file)
            
            if preview_file:
                preview_path = await StorageService.store_preview_file(
                    preview_file,
                    f"previews/{template.id}/v{new_version}/{preview_file.filename}"
                )
            
            # Create version record
            version = TemplateVersion(
                template_id=template.id,
                version_number=new_version,
                content_hash=content_hash or template.versions[-1].content_hash,
                template_file_path=template_path or template.template_file_url,
                preview_file_path=preview_path or template.preview_image_url,
                created_by=user_id,
                changes=changes,
                metadata=template.metadata
            )
            
            # Update template
            template.current_version = new_version
            template.latest_version = new_version
            template.total_versions += 1
            if template_path:
                template.template_file_url = template_path
            if preview_path:
                template.preview_image_url = preview_path
            
            db.add(version)
            return version
            
        except Exception as e:
            logger.error(f"Failed to create new version: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def _validate_template_files(
        template_file: UploadFile,
        preview_file: UploadFile
    ) -> None:
        """Validate template and preview files"""
        # Check extensions
        template_ext = os.path.splitext(template_file.filename)[1].lower()
        preview_ext = os.path.splitext(preview_file.filename)[1].lower()
        
        if template_ext not in TemplateManagementService.ALLOWED_TEMPLATE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid template file type. Allowed: {TemplateManagementService.ALLOWED_TEMPLATE_EXTENSIONS}"
            )
        
        if preview_ext not in TemplateManagementService.ALLOWED_PREVIEW_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid preview file type. Allowed: {TemplateManagementService.ALLOWED_PREVIEW_EXTENSIONS}"
            )
        
        # Check file sizes
        template_size = len(await template_file.read())
        preview_size = len(await preview_file.read())
        
        await template_file.seek(0)
        await preview_file.seek(0)
        
        if template_size > TemplateManagementService.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template file too large"
            )
        
        if preview_size > TemplateManagementService.MAX_FILE_SIZE:
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
    def _increment_version(version: str) -> str:
        """Increment semantic version number"""
        major, minor, patch = map(int, version.split("."))
        return f"{major}.{minor}.{patch + 1}"
    
    @staticmethod
    async def _calculate_file_hash(file: UploadFile) -> str:
        """Calculate SHA-256 hash of file contents"""
        sha256_hash = hashlib.sha256()
        while chunk := await file.read(8192):
            sha256_hash.update(chunk)
        await file.seek(0)
        return sha256_hash.hexdigest()
