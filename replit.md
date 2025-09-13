# Overview

MyTypist is a comprehensive document automation SaaS platform designed specifically for Nigerian businesses. The system enables users to create professional documents from templates with placeholder detection and replacement, integrated payment processing through Flutterwave, and enterprise-grade security features. The platform supports pay-as-you-go and subscription billing models with a robust token system for document generation.

**Status**: Successfully imported and configured for Replit environment. Backend is running on port 5000 and handling HTTP requests with 200 OK responses.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## 2025-09-13: GitHub Import and Replit Configuration
- Fixed critical pyproject.toml syntax errors (HTML entities, malformed TOML structure)
- Successfully installed Python 3.11 and all project dependencies using uv package manager
- Resolved complex SQLAlchemy model conflicts and import dependency issues
- Fixed Redis connection issues with proper fallback to mock Redis client for guest sessions
- Resolved SQLAlchemy relationship ambiguity in UserToken model (specified foreign_keys)
- Configured backend to run on port 5000 with host 0.0.0.0 as required for Replit
- Established PostgreSQL database connectivity through Replit's database integration
- Set up deployment configuration for VM deployment target
- Backend successfully starts, serves requests, and returns HTTP 200 responses

**Remaining Items for Production**:
- Run database migrations: `alembic upgrade head` to create tables
- Configure production security settings (SECRET_KEY, CORS, DEBUG=False)
- Set up Redis for production caching and Celery background tasks

# System Architecture

## Core Framework and Database
The system uses **FastAPI** as the primary web framework for high-performance API development with asynchronous support. **PostgreSQL** serves as the production database with advanced connection pooling, optimization configurations, and comprehensive migration support through Alembic. A **SQLite** fallback option is available for development environments.

## Document Processing Pipeline
The document automation system implements a sophisticated template processing engine using **python-docx** and **PyPDF2** for file manipulation. Templates support dynamic placeholder detection and replacement with intelligent formatting preservation. The system includes real-time document draft functionality, batch processing capabilities, and performance tracking with sub-500ms generation targets.

## Authentication and Security Architecture
Multi-layered security implementation includes **JWT-based authentication** with token rotation, **role-based access control** (Guest → User → Moderator → Admin), and comprehensive audit logging. Advanced security features include two-factor authentication, API key management, device fingerprinting, malware scanning, and real-time threat detection with automated incident response.

## Payment and Billing System
Integrated **Flutterwave payment gateway** handles multiple Nigerian payment methods including cards, bank transfers, and USSD. The system implements a flexible token-based economy with wallet management, subscription plans, and fraud prevention mechanisms. Payment processing includes webhook handling for transaction verification and automated billing cycles.

## Caching and Performance Layer
**Redis** provides high-performance caching, session management, and task queue support through **Celery** for asynchronous operations. The system includes intelligent caching strategies, connection pooling optimizations, and real-time performance monitoring with comprehensive analytics.

## Document Sharing and Collaboration
Advanced document sharing system with time-limited preview links, password protection, access logging, and view count tracking. Version control capabilities include document history, change tracking, and rollback functionality with automated backup systems.

# External Dependencies

## Payment Processing
- **Flutterwave API** for payment processing with support for Nigerian payment methods
- Webhook integration for real-time transaction status updates
- Multi-currency support with NGN as primary currency

## Database and Caching
- **PostgreSQL 13+** as primary production database with advanced optimization
- **Redis 6+** for caching, session storage, and task queue management
- **Alembic** for database schema migrations and version control

## Document Processing Libraries
- **python-docx** for Microsoft Word document manipulation
- **PyPDF2** and **PyMuPDF** for PDF processing and generation
- **Pillow (PIL)** for image processing and thumbnail generation
- **docx2pdf** for document format conversion

## Communication Services
- **Multi-provider email system** with SendGrid, Resend, and SMTP fallback
- **Firebase Cloud Messaging** for push notifications
- **Apple Push Notification service** for iOS notifications

## Development and Deployment
- **Gunicorn** with **Uvicorn workers** for production ASGI serving
- **Docker** containerization support for consistent deployments
- **Nginx** reverse proxy configuration for load balancing and SSL termination
- **Celery** distributed task queue for background job processing

## Security and Monitoring
- **bcrypt** and **scrypt** for password hashing with configurable rounds
- **pyotp** for TOTP-based two-factor authentication
- **Sentry** integration for real-time error monitoring and alerting
- **Advanced threat detection** with IOC database and ML-based anomaly detection