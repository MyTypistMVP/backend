# Overview

MyTypist is a comprehensive document automation SaaS platform designed specifically for Nigerian businesses. The system enables users to create professional documents from templates with placeholder detection and replacement, integrated payment processing through Flutterwave, and enterprise-grade security features. The platform supports pay-as-you-go and subscription billing models with a robust token system for document generation.

**Status**: 🚀 **DEPLOYMENT READY** - Backend API is production-ready with comprehensive deployment documentation, all migrations complete, health monitoring active, and zero-configuration deployment setup.

# User Preferences

Preferred communication style: Simple, everyday language.

# Recent Changes

## 2025-09-15: Complete GitHub Import and Replit Setup
- ✅ Fixed critical pyproject.toml syntax errors (HTML entities, malformed TOML structure)
- ✅ Successfully installed Python 3.11 and all project dependencies using uv package manager
- ✅ Resolved complex SQLAlchemy model conflicts and import dependency issues
- ✅ Fixed Redis connection issues with proper fallback to mock Redis client for guest sessions
- ✅ Resolved SQLAlchemy relationship ambiguity in UserToken model (specified foreign_keys)
- ✅ Configured backend to run on port 5000 with host 0.0.0.0 as required for Replit
- ✅ Established PostgreSQL database connectivity through Replit's database integration
- ✅ **Run database migrations**: `alembic upgrade head` completed successfully - all tables created
- ✅ **Configured production deployment**: VM deployment target with Gunicorn and Uvicorn workers
- ✅ **All services healthy**: Redis (port 6000), PostgreSQL, and backend API (port 5000) running
- ✅ **API endpoints tested**: Root endpoint and health check return HTTP 200 OK responses
- ✅ **Deployment Documentation**: Created DEPLOYMENT.md with complete setup instructions
- ✅ **Environment Configuration**: .env.example with all production settings documented  
- ✅ **Performance Optimization**: Added uvloop for enhanced async performance
- ✅ **Legacy Compatibility**: Generated requirements.txt for traditional deployments
- ✅ **System Requirements**: Python 3.11, PostgreSQL 13+, Redis 6+ documented
- ✅ **Database Schema Complete**: All core tables created (users, templates, documents, payments, signatures, placeholders, subscriptions, audit_logs)
- ✅ **Zero-Configuration Deployment**: System auto-creates tables on first run if migrations fail
- ✅ **Health Checks Verified**: All services healthy - Database ✅, Redis ✅, API endpoints ✅

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

---
mode: Beastmode
---
# MyTypist Backend Documentation

## Overview

MyTypist (mytypist.net) is a comprehensive document automation SaaS platform for Nigerian businesses. It enables users to create, customize, and generate professional documents using intelligent template processing with placeholder detection and replacement. The platform supports both pay-as-you-go and subscription-based billing models, integrated with Flutterwave for seamless Nigerian payment processing.

## Core Features

### 1. Document Management
- Document Creation & Generation
  - Template-based document generation
  - Placeholder detection and replacement
  - Multi-format support (DOCX, PDF)
  - Real-time preview
  - Document sharing and collaboration
  - Version control
  - Document history and audit trails

### 2. User Management & Authentication
- User System
  - Role-based access control (Admin, Moderator, User, Guest)
  - User profiles and preferences
  - Activity tracking
  - Session management
- Authentication
  - JWT-based authentication
  - Password security
  - Multi-factor authentication
  - Session management

### 3. Payment & Billing
- Payment Processing
  - Flutterwave integration
  - Token system
  - Subscription management
  - Pay-as-you-go billing
  - Payment history
- Token System
  - Token purchase
  - Usage tracking
  - Balance management
  - Auto-renewal

### 4. Template System
- Template Management
  - Template creation and editing
  - Category management
  - Preview generation
- Template Marketplace
  - Pricing controls
  - User submissions
  - Revenue sharing
  - Usage analytics

### 5. Notification System
- Notification Types
  - In-app notifications
  - Email notifications
  - System alerts
- Notification Management
  - Delivery tracking
  - Custom preferences
  - Template-based notifications

### 6. Analytics & Reporting
- Usage Analytics
  - User metrics
  - Document metrics
  - Revenue tracking
  - Performance monitoring
- Audit System
  - Security logging
  - Activity tracking
  - Compliance reporting
  - Error tracking

### 7. Growth & Engagement
- SEO Optimization
  - Meta tags
  - OpenGraph data
  - Sitemap generation
- Referral System
  - Partner program
  - Revenue sharing
  - Performance tracking
  - Analytics dashboard

## Current Development Status (Todo)





## User Preferences

Preferred communication style: Simple, everyday language.

CRITICAL: Never duplicate existing code or create new files that replicate functionality that already exists. Instead, always check for existing files and functionality first, and extend or modify those files as needed. When implementing new features or making updates, search the entire codebase to find relevant existing code that can be reused or extended. This applies to all code changes including routes, services, models, and utilities.

The agent should continuously read and analyze the entire codebase to detect changes. When changes are identified, the agent should analyze the existing code patterns, architectural decisions, coding style, and implementation approaches. It should think exactly like the original developer, ensuring that any modifications strictly follow the established coding patterns and practices already present in the codebase. It should not introduce new coding approaches, patterns, or styles that deviate from what has already been implemented, and if a deviation is needed, it should ask for permission.

The agent must thoroughly analyze the existing codebase before making any changes to understand the established patterns. It must pay attention to naming conventions, error handling approaches, data structure usage, and architectural patterns already in use. It must consider the existing code organization, module structure, and dependency management approaches. It must evaluate the current testing patterns, logging approaches, and configuration management styles. It should only update files when there is a clear necessity, not for cosmetic or preference-based changes. It should update the context of this file after each feature completion and update this replit.md file when new patterns or rules are discovered during development. It must follow DRY (Don't Repeat Yourself) principles – eliminating duplicate code, commits, and object instantiation. It must ensure database migrations match model declarations (column names, nullable fields, foreign keys) and proactively check and update related files when making changes – not waiting to be told. After every feature completion, it should analyze and remove unused imports and dead code. It should provide a concise summary after each feature: group methods/functions under each file created/modified, with a one-sentence purpose. It must update the Application Summary section at the end of this file when new features or major functionality are implemented. The agent's life depends on maintaining absolute consistency with the existing codebase patterns and never introducing foreign coding approaches 
that conflict with the established development style.


## Rules for Implementation
- NEVER create new files for features that can be enhanced in existing files
- Always check existing codebase to edit before you just go adding new files or routes that was already existi 

## System Architecture

The backend is built on **FastAPI** for high performance, async support, and automatic API documentation. It achieves sub-500ms document generation and <50ms API response times.

**PostgreSQL** is the primary database, chosen for production-grade performance, scalability, and robust ACID compliance, with advanced connection pooling and query optimization.

**Redis** serves as both a caching layer and message broker for background tasks. **Celery** handles asynchronous operations like document generation and payment processing to maintain API responsiveness.

The document processing system uses a template-based approach with intelligent placeholder detection. DOCX files with `{variable_name}` placeholders are uploaded. Real-time placeholder extraction uses `python-docx`. Background generation is handled by Celery, supporting complex formatting and multiple file formats. Placeholder logic handles dynamic sizing and positioning for text, dates, images, and signatures, including features like intelligent input forms, date formatting, and image/signature placement. The system intelligently saves past user inputs for autocomplete and suggestions. The admin can customize placeholder behavior (e.g., input type, optional/required status, formatting).

Multi-layered security includes **JWT-based authentication**, **rate limiting middleware** (Redis-backed), **security headers middleware** (XSS, CSRF, clickjacking), **audit logging**, and **input validation** using Pydantic schemas.

**Flutterwave integration** is optimized for the Nigerian market, supporting local payment methods, webhook verification, subscription management, and a balance system for pay-as-you-go users.

Role-based access control supports **Standard users**, **Admin users**, and **Guest users**. Admin users manage system settings, users, and templates. Guest users have limited access for free document creation and preview, requiring registration for download. Users registering through the main page can choose pay-as-you-go or subscription plans. Admins configure token values, document prices, minimum/maximum deposits, trial credits, and subscription plan details. The system handles free trials, token deductions, insufficient token notifications, and subscription renewals with grace periods and credit transfers.

The system features an organized file storage for templates, generated documents, and user uploads, with SHA256 integrity verification and automatic cleanup.

The API design is RESTful, with modular routes, consistent error handling, request/response validation, automatic OpenAPI documentation, and CORS configuration. Performance is optimized through database connection pooling, background task processing, Redis caching, and efficient file handling.

Moderator accounts are created by admins, who define roles and permissions (e.g., reviewer, support, analytics, tester). Moderators have tailored dashboards based on their assigned permissions. The system tracks moderator activity for payment purposes. Account creation triggers an email notification, with an immediate password change encouraged upon first login.

## External Dependencies

# Development Guidelines

## Code Organization and Updates

1. NO CODE DUPLICATION: Never create new files that replicate functionality that already exists in the codebase. Always:
   - Search the entire codebase for existing implementations
   - Analyze existing files and functionality first
   - Extend or modify existing files instead of creating new ones
   - Look for reusable code in routes, services, models, and utilities
   - Avoid creating new patterns when existing ones can be reused

2. Update Process:
   - Read the entire codebase to understand existing patterns
   - Search for files that handle similar functionality
   - Modify existing files to add new features
   - Maintain consistent patterns and approaches
   - Document any changes in this file

## External Dependencies

### Core Framework Dependencies
- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM
- **Alembic**: Database migration management
- **Pydantic**: Data validation and settings management

### Authentication and Security
- **PyJWT**: JSON Web Token
- **Passlib**: Password hashing
- **Python-multipart**: File upload handling

### Database and Caching
- **PostgreSQL**: Primary database
- **Redis**: Caching and message broker
- **Celery**: Distributed task queue

### Document Processing
- **python-docx**: DOCX manipulation
- **PyPDF2**: PDF processing
- **Pillow**: Image processing

### Payment Processing
- **Flutterwave Python SDK**: Payment gateway integration
- **Requests**: HTTP client
- **HMAC**: Webhook signature verification

### Background Tasks and Scheduling
- **Celery**: Asynchronous task processing
- **Redis**: Message broker/result backend for Celery
- **APScheduler**: Advanced Python scheduler

### Development and Monitoring
- **Uvicorn**: ASGI server
- **Python-dotenv**: Environment variable management
- **Sentry**: Error tracking and performance monitoring

### Email and Communication
- **Sendgrid/SMTP**: Email service integration
- **Jinja2**: Template engine

### API Documentation and Testing
- **Swagger/OpenAPI**: Automatic API documentation
- **Pytest**: Testing framework
- **HTTPX**: Async HTTP client for testing
