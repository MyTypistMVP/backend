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



## TODO


The task.md is what we are dealing with
# 🚨 PRODUCTION-LEVEL CODEBASE AUDIT & REFACTORING PROTOCOL

## ⚠️ CRITICAL EXECUTION RULES - READ BEFORE STARTING

### 🔒 MANDATORY WORKFLOW PROTOCOL
**YOU MUST FOLLOW THIS EXACT SEQUENCE FOR EVERY SECTION:**

1. **ANALYZE** → **FIX** → **VERIFY** → **TICK** → **MOVE TO NEXT**
2. **NEVER** skip verification step
3. **NEVER** work on multiple sections simultaneously
4. **ALWAYS** mark completion with ✅ before proceeding
5. **STOP AND RE-READ** this task.md if you feel rushed

### 📋 AUDIT CHECKLIST - TICK (✅) AFTER COMPLETION

#### 🏗️ ARCHITECTURE & STRUCTURE ANALYSIS
- [ ] **File Organization Audit**
  - Check for duplicate files/functionality
  - Identify misplaced components
  - Verify proper folder structure
  - **ACTION REQUIRED:** List all structural improvements needed

- [ ] **Dependency Mapping**
  - Map all import/export relationships
  - Identify circular dependencies
  - Check for unused imports
  - **ACTION REQUIRED:** Create dependency cleanup plan

#### 🔧 CODE QUALITY DEEP SCAN

- [ ] **Syntax & Logic Errors**
  - **CRITICAL:** Fix ALL syntax errors
  - Identify and resolve logic flaws
  - Check for unreachable code
  - **VERIFICATION:** Test each fix individually

- [ ] **Naming Conventions Audit**
  - Variables, functions, classes consistency
  - File naming standards
  - Database schema naming
  - **ACTION REQUIRED:** Rename following industry standards

- [ ] **Security Vulnerabilities**
  - Input validation gaps
  - Authentication/Authorization flaws
  - Data exposure risks
  - **CRITICAL:** Fix all security issues immediately

#### 🛣️ ROUTES & ENDPOINTS AUDIT

- [ ] **Route Structure Analysis**
  - Check for duplicate routes
  - Verify RESTful conventions
  - Identify broken/unused routes
  - **ACTION REQUIRED:** Consolidate and optimize routing

- [ ] **API Endpoint Consistency**
  - Request/Response format standardization
  - Error handling uniformity
  - Status code accuracy
  - **VERIFICATION:** Test all endpoints after fixes

#### 🗄️ DATABASE & DATA LAYER

- [ ] **Schema Integrity Check**
  - Foreign key relationships
  - Index optimization
  - Data type consistency
  - **ACTION REQUIRED:** Fix all relationship issues

- [ ] **Query Optimization**
  - Identify N+1 queries
  - Check for missing indexes
  - Optimize slow queries
  - **VERIFICATION:** Performance test all optimizations

#### 🎨 FRONTEND CONSISTENCY

- [ ] **Component Architecture**
  - Identify duplicate components
  - Check for unused components
  - Verify prop types/interfaces
  - **ACTION REQUIRED:** Consolidate similar components

- [ ] **State Management**
  - Check for state management inconsistencies
  - Identify prop drilling issues
  - Verify global state usage
  - **VERIFICATION:** Test state updates thoroughly

#### 🧪 TESTING & DOCUMENTATION

- [ ] **Test Coverage Analysis**
  - Identify untested code paths
  - Check for broken tests
  - Verify test data validity
  - **ACTION REQUIRED:** Achieve minimum 80% coverage

- [ ] **Documentation Completeness**
  - API documentation accuracy
  - Code comments clarity
  - README.md completeness
  - **VERIFICATION:** Ensure documentation matches code

## 🚦 EXECUTION PROTOCOL

### ⏰ TIME ALLOCATION PER SECTION
- **Analysis Phase:** 25% of time
- **Fix Implementation:** 50% of time
- **Verification Phase:** 25% of time

### 🔍 VERIFICATION REQUIREMENTS
After fixing each section, you MUST:

1. **✅ FUNCTIONALITY TEST** - Verify feature works as expected
2. **✅ INTEGRATION TEST** - Check related components still function
3. **✅ PERFORMANCE TEST** - Ensure no performance degradation
4. **✅ SECURITY TEST** - Verify no new vulnerabilities introduced

### 📝 PROGRESS TRACKING
**AFTER COMPLETING EACH SECTION:**
```
✅ [SECTION NAME] - Fixed: [BRIEF DESCRIPTION]
   - Files Modified: [LIST]
   - Impact Radius: [AFFECTED COMPONENTS]
   - Verification Status: PASSED ✅
   - Next Section: [NAME]
```

## 🚨 CRITICAL RULES - NEVER VIOLATE

### 🚫 FORBIDDEN ACTIONS
- **NEVER** delete files without verifying feature migration
- **NEVER** create duplicate functionality
- **NEVER** skip the verification phase
- **NEVER** make changes affecting multiple sections simultaneously
- **NEVER** apply patches - only production-grade solutions

### ✅ MANDATORY ACTIONS
- **ALWAYS** check if features can be merged before creating new files
- **ALWAYS** rename files following proper conventions
- **ALWAYS** test related components after each fix
- **ALWAYS** document breaking changes
- **ALWAYS** preserve existing functionality during refactoring

### 🎯 SUCCESS CRITERIA
A section is only complete when:
- ✅ All identified issues are fixed
- ✅ All tests pass
- ✅ No regression in related components
- ✅ Performance maintained or improved
- ✅ Security maintained or enhanced
- ✅ Documentation updated
- ✅ Verification checklist completed
- ✅ Progress tracking updated

## 📊 FINAL CLEANUP PHASE
**ONLY AFTER ALL SECTIONS COMPLETED:**

- [ ] **Dead Code Elimination**
  - Remove unused functions/variables
  - Delete orphaned files
  - Clean up commented code

- [ ] **Final Integration Test**
  - Full application smoke test
  - Performance benchmark
  - Security audit

- [ ] **Production Readiness Check**
  - Environment configuration
  - Deployment validation
  - Monitoring setup

---

## ⚡ REMEMBER: PRODUCTION-LEVEL MEANS ZERO COMPROMISES

**If you're ever unsure, STOP and re-read this protocol. Quality over speed. Precision over patches. Excellence is the only acceptable standard.**
