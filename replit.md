# Overview

MyTypist is a comprehensive document automation SaaS platform for Nigerian businesses. It allows users to create professional documents from templates with intelligent placeholder detection and replacement. The platform integrates Flutterwave for payment processing, supports pay-as-you-go and subscription billing models, and features robust security.

# User Preferences

Preferred communication style: Simple, everyday language.

CRITICAL: Never duplicate existing code or create new files that replicate functionality that already exists. Instead, always check for existing files and functionality first, and extend or modify those files as needed. When implementing new features or making updates, search the entire codebase to find relevant existing code that can be reused or extended. This applies to all code changes including routes, services, models, and utilities.

The agent should continuously read and analyze the entire codebase to detect changes. When changes are identified, the agent should analyze the existing code patterns, architectural decisions, coding style, and implementation approaches. It should think exactly like the original developer, ensuring that any modifications strictly follow the established coding patterns and practices already present in the codebase. It should not introduce new coding approaches, patterns, or styles that deviate from what has already been implemented, and if a deviation is needed, it should ask for permission.

The agent must thoroughly analyze the existing codebase before making any changes to understand the established patterns. It must pay attention to naming conventions, error handling approaches, data structure usage, and architectural patterns already in use. It must consider the existing code organization, module structure, and dependency management approaches. It must evaluate the current testing patterns, logging approaches, and configuration management styles. It should only update files when there is a clear necessity, not for cosmetic or preference-based changes. It should update the context of this file after each feature completion and update this replit.md file when new patterns or rules are discovered during development. It must follow DRY (Don't Repeat Yourself) principles – eliminating duplicate code, commits, and object instantiation. It must ensure database migrations match model declarations (column names, nullable fields, foreign keys) and proactively check and update related files when making changes – not waiting to be told. After every feature completion, it should analyze and remove unused imports and dead code. It should provide a concise summary after each feature: group methods/functions under each file created/modified, with a one-sentence purpose. It must update the Application Summary section at the end of this file when new features or major functionality are implemented. The agent's life depends on maintaining absolute consistency with the existing codebase patterns and never introducing foreign coding approaches that conflict with the established development style.

# System Architecture

The backend is built on **FastAPI** for high performance and asynchronous operations. **PostgreSQL** is the primary database, managed with Alembic for migrations, with SQLite for development. **Redis** is used for caching, session management, and as a message broker for **Celery** for background tasks.

The document processing system uses **python-docx** and **PyPDF2** for template-based document generation, supporting dynamic placeholder detection and replacement with intelligent formatting. It includes real-time draft functionality and batch processing.

Security is multi-layered, featuring **JWT-based authentication** with token rotation, **role-based access control** (Guest, User, Moderator, Admin), audit logging, rate limiting, and input validation with Pydantic.

The payment system integrates **Flutterwave** for Nigerian payment methods, supporting a flexible token-based economy, subscription plans, and fraud prevention with webhook handling.

Document sharing includes time-limited preview links, password protection, and version control.
Moderator accounts are created by admins with tailored dashboards based on assigned permissions.

# External Dependencies

## Payment Processing
- **Flutterwave API**

## Database and Caching
- **PostgreSQL**
- **Redis**
- **Alembic**

## Document Processing Libraries
- **python-docx**
- **PyPDF2**
- **Pillow**
- **docx2pdf**

## Communication Services
- **SendGrid/SMTP** (multi-provider email system)
- **Firebase Cloud Messaging**
- **Apple Push Notification service**

## Development and Deployment
- **FastAPI**
- **Gunicorn**
- **Uvicorn**
- **Docker**
- **Nginx**
- **Celery**
- **SQLAlchemy**
- **Pydantic**
- **PyJWT**
- **Passlib**
- **Python-multipart**
- **Requests**
- **HMAC**
- **APScheduler**

## Security and Monitoring
- **bcrypt**
- **scrypt**
- **pyotp**
- **Sentry**