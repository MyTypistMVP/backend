"""
Tests for document sharing functionality
"""
from datetime import datetime
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.document import Document
from app.models.visit import Visit
from app.routes.document_sharing import router
from database import Base, get_db

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test app
app = FastAPI()
app.include_router(router)

# Setup test database
Base.metadata.create_all(bind=engine)
    # Test document retrieval
    response = client.get(f"/document-sharing/document/{doc.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["content"] == "Test content"
    assert not data["watermark"]  # No watermark for downloaded documents

def test_get_shared_template(db: Session):
    # Create test template
    doc = Document(
        title="Test Template",
        content="Template content",
        is_downloaded=False,
        is_public=True
    )
    db.add(doc)
    db.commit()

    # Test template retrieval
    response = client.get(f"/document-sharing/document/{doc.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Template"
    assert data["content"] == "Template content"
    assert data["watermark"]  # Watermark for public templates

def test_visit_tracking(db: Session):
    # Create test document
    doc = Document(
        title="Test Document",
        content="Test content",
        is_public=True
    )
    db.add(doc)
    db.commit()

    # Simulate multiple visits
    client.get(f"/document-sharing/document/{doc.id}")
    client.get(f"/document-sharing/document/{doc.id}")  # Same IP, should count as one unique visitor

    # Test analytics
    response = client.get(f"/document-sharing/analytics/{doc.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_views"] == 2
    assert data["unique_visitors"] == 1

def test_document_not_found():
    response = client.get("/document-sharing/document/999999")
    # Create test document
    doc = Document(
        title="Test Document",
        content="Test content",
        is_public=True
    )
    db.add(doc)
    db.commit()

    # Simulate multiple visits
    client.get(f"/document/{doc.id}")
    client.get(f"/document/{doc.id}")  # Same IP, should count as one unique visitor

    # Test analytics
    response = client.get(f"/analytics/{doc.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["total_views"] == 2
    assert data["unique_visitors"] == 1

def test_document_not_found():
    response = client.get("/document/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found"