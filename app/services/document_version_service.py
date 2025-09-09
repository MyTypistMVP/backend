"""
Document Version Control System
Track document changes and allow users to view/restore older versions
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, desc
from database import Base

logger = logging.getLogger(__name__)


class DocumentVersion(Base):
    """Document version history tracking"""
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)

    # Version data
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    placeholder_data = Column(Text, nullable=True)  # JSON string of placeholder values
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)

    # Change tracking
    change_summary = Column(Text, nullable=True)  # What was changed
    changed_by = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    change_type = Column(String(50), nullable=False)  # create, edit, restore

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_current = Column(Boolean, default=False, index=True)

    # Performance data
    generation_time = Column(Integer, nullable=True)  # milliseconds
    estimated_time_saved = Column(Integer, nullable=True)  # minutes saved vs manual creation


class DocumentVersionService:
    """Service for managing document versions and change tracking"""

    @staticmethod
    def create_version(
        db: Session,
        document_id: int,
        user_id: int,
        title: str,
        content: Optional[str] = None,
        placeholder_data: Optional[Dict[str, Any]] = None,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None,
        change_summary: Optional[str] = None,
        change_type: str = "create",
        generation_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a new document version"""
        try:
            # Get current version number
            latest_version = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(desc(DocumentVersion.version_number)).first()

            next_version = (latest_version.version_number + 1) if latest_version else 1

            # Mark all previous versions as not current
            db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id,
                DocumentVersion.is_current == True
            ).update({"is_current": False})

            # Calculate estimated time saved (rough estimation)
            estimated_time_saved = DocumentVersionService._calculate_time_saved(
                placeholder_data, generation_time
            )

            # Create new version
            version = DocumentVersion(
                document_id=document_id,
                version_number=next_version,
                title=title,
                content=content,
                placeholder_data=json.dumps(placeholder_data) if placeholder_data else None,
                file_path=file_path,
                file_size=file_size,
                change_summary=change_summary or f"Document {change_type}",
                changed_by=user_id,
                change_type=change_type,
                is_current=True,
                generation_time=generation_time,
                estimated_time_saved=estimated_time_saved
            )

            db.add(version)
            db.commit()
            db.refresh(version)

            logger.info(f"Created document version {next_version} for document {document_id}")

            return {
                "success": True,
                "version_id": version.id,
                "version_number": version.version_number,
                "document_id": document_id,
                "change_type": change_type,
                "generation_time": generation_time,
                "estimated_time_saved": estimated_time_saved,
                "created_at": version.created_at.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to create document version: {e}")
            raise

    @staticmethod
    def get_document_versions(
        db: Session,
        document_id: int,
        user_id: int,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Get version history for a document"""
        try:
            # Verify user has access to document
            from app.models.document import Document
            document = db.query(Document).filter(
                Document.id == document_id
            ).first()

            if not document:
                return {"success": False, "error": "Document not found"}

            # Check if user owns document or is admin
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if document.user_id != user_id and not (user and user.is_admin):
                return {"success": False, "error": "Access denied"}

            # Get versions
            versions = db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(desc(DocumentVersion.version_number)).limit(limit).all()

            # Format version data
            version_data = []
            for version in versions:
                # Get user info
                user = db.query(User).filter(User.id == version.changed_by).first()

                version_data.append({
                    "version_id": version.id,
                    "version_number": version.version_number,
                    "title": version.title,
                    "change_summary": version.change_summary,
                    "change_type": version.change_type,
                    "is_current": version.is_current,
                    "created_at": version.created_at.isoformat(),
                    "changed_by": {
                        "id": user.id if user else None,
                        "name": f"{user.first_name} {user.last_name}" if user else "Unknown",
                        "email": user.email if user else "Unknown"
                    },
                    "file_size": version.file_size,
                    "generation_time": version.generation_time,
                    "estimated_time_saved": version.estimated_time_saved
                })

            return {
                "success": True,
                "document_id": document_id,
                "versions": version_data,
                "total_versions": len(version_data),
                "current_version": versions[0].version_number if versions else 0
            }

        except Exception as e:
            logger.error(f"Failed to get document versions: {e}")
            raise

    @staticmethod
    def get_version_details(
        db: Session,
        version_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Get detailed information about a specific version"""
        try:
            version = db.query(DocumentVersion).filter(
                DocumentVersion.id == version_id
            ).first()

            if not version:
                return {"success": False, "error": "Version not found"}

            # Verify user has access
            from app.models.document import Document
            document = db.query(Document).filter(
                Document.id == version.document_id
            ).first()

            if not document:
                return {"success": False, "error": "Document not found"}

            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if document.user_id != user_id and not (user and user.is_admin):
                return {"success": False, "error": "Access denied"}

            # Get user who made the change
            changed_by_user = db.query(User).filter(User.id == version.changed_by).first()

            return {
                "success": True,
                "version": {
                    "id": version.id,
                    "version_number": version.version_number,
                    "document_id": version.document_id,
                    "title": version.title,
                    "content": version.content,
                    "placeholder_data": json.loads(version.placeholder_data) if version.placeholder_data else {},
                    "file_path": version.file_path,
                    "file_size": version.file_size,
                    "change_summary": version.change_summary,
                    "change_type": version.change_type,
                    "is_current": version.is_current,
                    "created_at": version.created_at.isoformat(),
                    "changed_by": {
                        "id": changed_by_user.id if changed_by_user else None,
                        "name": f"{changed_by_user.first_name} {changed_by_user.last_name}" if changed_by_user else "Unknown",
                        "email": changed_by_user.email if changed_by_user else "Unknown"
                    },
                    "generation_time": version.generation_time,
                    "estimated_time_saved": version.estimated_time_saved
                }
            }

        except Exception as e:
            logger.error(f"Failed to get version details: {e}")
            raise

    @staticmethod
    def restore_version(
        db: Session,
        version_id: int,
        user_id: int,
        restore_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Restore a previous version as the current version"""
        try:
            # Get the version to restore
            old_version = db.query(DocumentVersion).filter(
                DocumentVersion.id == version_id
            ).first()

            if not old_version:
                return {"success": False, "error": "Version not found"}

            # Verify user has access
            from app.models.document import Document
            document = db.query(Document).filter(
                Document.id == old_version.document_id
            ).first()

            if not document:
                return {"success": False, "error": "Document not found"}

            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if document.user_id != user_id and not (user and user.is_admin):
                return {"success": False, "error": "Access denied"}

            # Create new version based on the old one
            change_summary = restore_reason or f"Restored to version {old_version.version_number}"

            restore_result = DocumentVersionService.create_version(
                db=db,
                document_id=old_version.document_id,
                user_id=user_id,
                title=old_version.title,
                content=old_version.content,
                placeholder_data=json.loads(old_version.placeholder_data) if old_version.placeholder_data else None,
                file_path=old_version.file_path,
                file_size=old_version.file_size,
                change_summary=change_summary,
                change_type="restore"
            )

            # Update the main document record
            document.title = old_version.title
            document.content = old_version.content
            document.file_path = old_version.file_path
            document.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Restored document {old_version.document_id} to version {old_version.version_number}")

            return {
                "success": True,
                "message": f"Document restored to version {old_version.version_number}",
                "restored_from_version": old_version.version_number,
                "new_version": restore_result["version_number"],
                "document_id": old_version.document_id
            }

        except Exception as e:
            logger.error(f"Failed to restore version: {e}")
            raise

    @staticmethod
    def compare_versions(
        db: Session,
        version_id_1: int,
        version_id_2: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Compare two document versions"""
        try:
            version1 = db.query(DocumentVersion).filter(
                DocumentVersion.id == version_id_1
            ).first()

            version2 = db.query(DocumentVersion).filter(
                DocumentVersion.id == version_id_2
            ).first()

            if not version1 or not version2:
                return {"success": False, "error": "One or both versions not found"}

            if version1.document_id != version2.document_id:
                return {"success": False, "error": "Versions are from different documents"}

            # Verify user has access
            from app.models.document import Document
            document = db.query(Document).filter(
                Document.id == version1.document_id
            ).first()

            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if document.user_id != user_id and not (user and user.is_admin):
                return {"success": False, "error": "Access denied"}

            # Compare versions
            changes = []

            # Title comparison
            if version1.title != version2.title:
                changes.append({
                    "field": "title",
                    "old_value": version1.title,
                    "new_value": version2.title
                })

            # Content comparison (basic)
            if version1.content != version2.content:
                changes.append({
                    "field": "content",
                    "old_length": len(version1.content or ""),
                    "new_length": len(version2.content or ""),
                    "changed": True
                })

            # Placeholder data comparison
            old_placeholders = json.loads(version1.placeholder_data) if version1.placeholder_data else {}
            new_placeholders = json.loads(version2.placeholder_data) if version2.placeholder_data else {}

            placeholder_changes = []
            all_keys = set(old_placeholders.keys()) | set(new_placeholders.keys())

            for key in all_keys:
                old_val = old_placeholders.get(key, "")
                new_val = new_placeholders.get(key, "")

                if old_val != new_val:
                    placeholder_changes.append({
                        "placeholder": key,
                        "old_value": old_val,
                        "new_value": new_val
                    })

            return {
                "success": True,
                "comparison": {
                    "version_1": {
                        "id": version1.id,
                        "version_number": version1.version_number,
                        "created_at": version1.created_at.isoformat()
                    },
                    "version_2": {
                        "id": version2.id,
                        "version_number": version2.version_number,
                        "created_at": version2.created_at.isoformat()
                    },
                    "changes": changes,
                    "placeholder_changes": placeholder_changes,
                    "total_changes": len(changes) + len(placeholder_changes)
                }
            }

        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            raise

    @staticmethod
    def _calculate_time_saved(
        placeholder_data: Optional[Dict[str, Any]],
        generation_time: Optional[int]
    ) -> int:
        """
        Calculate estimated time saved vs manual document creation
        Returns time in minutes
        """
        if not placeholder_data:
            return 5  # Base time saved for any document generation

        # Rough calculation based on document complexity
        base_time = 10  # 10 minutes base for any document
        placeholder_count = len(placeholder_data)

        # Add time based on placeholder types and complexity
        time_per_placeholder = 2  # 2 minutes per placeholder on average

        # Bonus time for complex placeholders
        complex_placeholders = ["signature", "image", "address", "date"]
        bonus_time = 0

        for key, value in placeholder_data.items():
            if any(complex_type in key.lower() for complex_type in complex_placeholders):
                bonus_time += 5  # 5 extra minutes for complex placeholders

        total_estimated = base_time + (placeholder_count * time_per_placeholder) + bonus_time

        # Factor in actual generation time (faster generation = more time saved)
        if generation_time and generation_time < 10000:  # Less than 10 seconds
            total_estimated += 5  # Bonus for fast generation

        return min(total_estimated, 120)  # Cap at 2 hours maximum

    @staticmethod
    def get_user_time_savings(
        db: Session,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get total time savings for a user over a period"""
        try:
            from datetime import timedelta
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get all versions created by user in the period
            versions = db.query(DocumentVersion).filter(
                DocumentVersion.changed_by == user_id,
                DocumentVersion.created_at >= start_date,
                DocumentVersion.estimated_time_saved.isnot(None)
            ).all()

            total_time_saved = sum(v.estimated_time_saved for v in versions)
            total_documents = len(versions)
            avg_generation_time = sum(v.generation_time for v in versions if v.generation_time) / len(versions) if versions else 0

            return {
                "success": True,
                "user_id": user_id,
                "period_days": days,
                "statistics": {
                    "total_time_saved_minutes": total_time_saved,
                    "total_time_saved_hours": round(total_time_saved / 60, 2),
                    "total_documents_created": total_documents,
                    "average_time_saved_per_document": round(total_time_saved / total_documents, 2) if total_documents > 0 else 0,
                    "average_generation_time_ms": round(avg_generation_time, 2),
                    "productivity_boost": f"{round((total_time_saved / max(total_documents * 30, 1)) * 100, 1)}%"  # vs 30 min manual creation
                }
            }

        except Exception as e:
            logger.error(f"Failed to get user time savings: {e}")
            raise
