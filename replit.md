# MyTypist Backend Documentation

## Overview

MyTypist (mytypist.net) is a comprehensive document automation SaaS platform for Nigerian businesses. It enables users to create, customize, and generate professional documents using intelligent template processing with placeholder detection and replacement. The platform supports both pay-as-you-go and subscription-based billing models, integrated with Flutterwave for seamless Nigerian payment processing.

The system is a high-performance, production-ready FastAPI backend handling document generation, template management, digital signatures, user management, and payment processing with robust security and audit trails. Key capabilities include sub-500ms document processing, advanced batch processing, signature canvas integration, smart template upload/analysis, real-time draft management, and enterprise-grade security.

## User Preferences

Preferred communication style: Simple, everyday language.
The agent should continuously read and analyze the entire codebase to detect changes. When changes are identified, the agent should analyze the existing code patterns, architectural decisions, coding style, and implementation approaches. It should think exactly like the original developer, ensuring that any modifications strictly follow the established coding patterns and practices already present in the codebase. It should not introduce new coding approaches, patterns, or styles that deviate from what has already been implemented, and if a deviation is needed, it should ask for permission.
The agent must thoroughly analyze the existing codebase before making any changes to understand the established patterns. It must pay attention to naming conventions, error handling approaches, data structure usage, and architectural patterns already in use. It must consider the existing code organization, module structure, and dependency management approaches. It must evaluate the current testing patterns, logging approaches, and configuration management styles. It should only update files when there is a clear necessity, not for cosmetic or preference-based changes. It should update the context of this file after each feature completion and update this replit.md file when new patterns or rules are discovered during development. It must follow DRY (Don't Repeat Yourself) principles – eliminating duplicate code, commits, and object instantiation. It must ensure database migrations match model declarations (column names, nullable fields, foreign keys) and proactively check and update related files when making changes – not waiting to be told. After every feature completion, it should analyze and remove unused imports and dead code. It should provide a concise summary after each feature: group methods/functions under each file created/modified, with a one-sentence purpose. It must update the Application Summary section at the end of this file when new features or major functionality are implemented. The agent's life depends on maintaining absolute consistency with the existing codebase patterns and never introducing foreign coding approaches that conflict with the established development style.

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