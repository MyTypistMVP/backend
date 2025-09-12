"""
Template Management Models
Enhanced models for template management with versioning and metadata
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base

# Association table for template categories
template_categories = Table(
    'template_categories',
    Base.metadata,
    Column('template_id', Integer, ForeignKey('templates.id')),
    Column('category_id', Integer, ForeignKey('template_categories.id'))
)

class TemplateCategory(Base):
    """Category model for organizing templates"""
    __tablename__ = 'template_categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(String)
    parent_id = Column(Integer, ForeignKey('template_categories.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    parent = relationship("TemplateCategory", remote_side=[id], backref="subcategories")
    templates = relationship("Template", secondary=template_categories, back_populates="categories")



    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False)
    version_number = Column(String, nullable=False)  # Semantic versioning
    content_hash = Column(String, nullable=False)  # Hash of template content
    preview_file_path = Column(String)
    template_file_path = Column(String)
    changes = Column(JSON)  # List of changes in this version
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON)  # Additional version-specific metadata

    # Relationships
    template = relationship("Template", back_populates="versions")
    creator = relationship("User")

class Template(Base):
    """Enhanced template model with versioning and metadata support"""
    __tablename__ = 'templates'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    description = Column(String)
    current_version = Column(String)  # Current active version number
    preview_image_url = Column(String)
    template_file_url = Column(String)
    placeholder_schema = Column(JSON)  # Schema for template placeholders
    metadata = Column(JSON)  # Template metadata (tags, requirements, etc)
    is_public = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    approval_status = Column(String)  # pending, approved, rejected
    approval_notes = Column(String)
    created_by = Column(Integer, ForeignKey('users.id'))
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Version tracking
    first_version = Column(String)
    latest_version = Column(String)
    total_versions = Column(Integer, default=1)
    
    # Usage statistics
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    rating = Column(Integer)
    review_count = Column(Integer, default=0)
    
    # Relationships
    categories = relationship("TemplateCategory", secondary=template_categories, back_populates="templates")
    versions = relationship("TemplateVersion", back_populates="template", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])

class TemplateReview(Base):
    """User reviews and ratings for templates"""
    __tablename__ = 'template_reviews'

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 rating
    review_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    template = relationship("Template")
    user = relationship("User")
