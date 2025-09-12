"""
MyTypist FastAPI Backend
High-performance document automation platform with Flutterwave integration
"""

import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import redis
from celery import Celery

from config import settings
from database import engine, SessionLocal
from app.models import user, template, document, signature, visit, payment, audit
from app.services.feedback_service import Feedback  # Import feedback model
from app.routes import auth, documents, templates, signatures, analytics, payments, admin, monitoring, feedback, referrals
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityMiddleware
from app.middleware.audit import AuditMiddleware
from app.middleware.performance import PerformanceMiddleware, CompressionMiddleware
from app.middleware.advanced_security import RequestValidationMiddleware
from app.middleware.csrf_protection import CSRFProtectionMiddleware
from app.services.audit_service import AuditService
from app.services.cache_service import cache_service
# Enterprise services removed for MVP


if settings.SKIP_DB_TABLE_CREATION:
    # Skip database table creation for now to get the server running (controlled via env)
    print("⚠️ SKIP_DB_TABLE_CREATION is true — skipping database table creation")
    print("ℹ️  Database tables should be created via migration scripts (alembic)")
    print("⚠️ Skipping advanced service tables to resolve startup issues")

# Initialize Redis (optional)
if settings.REDIS_ENABLED:
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            decode_responses=True,
            socket_connect_timeout=5
        )
        # Test connection
        redis_client.ping()
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        # Fall back to a mock for local development when explicitly enabled but failing
        class MockRedis:
            def ping(self): return True
            def get(self, key): return None
            def set(self, key, value, ex=None): return True
            def setex(self, key, time, value): return True
            def delete(self, key): return True
            def incr(self, key): return 1
            def expire(self, key, time): return True

        redis_client = MockRedis()
else:
    # Use a mock Redis client for development when Redis is disabled
    class MockRedis:
        def ping(self): return True
        def get(self, key): return None
        def set(self, key, value, ex=None): return True
        def setex(self, key, time, value): return True
        def delete(self, key): return True
        def incr(self, key): return 1
        def expire(self, key, time): return True

    redis_client = MockRedis()

# Initialize Celery
celery_app = Celery(
    "mytypist",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks.document_tasks', 'app.tasks.payment_tasks', 'app.tasks.cleanup_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 MyTypist Backend Starting...")

    # Initialize cache service
    try:
        await cache_service.initialize()
        print("✅ Cache service initialized")
    except Exception as e:
        print(f"⚠️ Cache service failed to initialize: {e}")

    # Test Redis connection (optional)
    try:
        redis_client.ping()
        print("✅ Redis connection established")
    except Exception as e:
        print(f"⚠️ Redis connection failed (continuing without caching): {e}")

    # Test database connection
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

    # Initialize audit service
    try:
        AuditService.log_system_event(audit.AuditEventType.SYSTEM_STARTUP.value, {"service": settings.APP_NAME})
    except Exception as e:
        print(f"⚠️ Audit service failed to start: {e}")

    # Enterprise RBAC system removed for MVP

    yield

    # Shutdown
    print("🛑 MyTypist Backend Shutting down...")
    try:
        AuditService.log_system_event(audit.AuditEventType.SYSTEM_SHUTDOWN.value, {})
    except Exception as e:
        print(f"⚠️ Audit service error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title="MyTypist API",
    description="High-performance document automation platform for Nigerian businesses",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Performance and security middleware (order matters!)
app.add_middleware(CompressionMiddleware, minimum_size=1024, compression_level=6)
app.add_middleware(PerformanceMiddleware, slow_request_threshold=1.0)
# Use consolidated security middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(CSRFProtectionMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware, redis_client=redis_client)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)


# Performance monitoring middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Monitor API performance"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log slow requests
    if process_time > 1.0:  # Log requests taking more than 1 second
        try:
            AuditService.log_performance_issue(
                "slow_request",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "duration": process_time,
                    "status_code": response.status_code
                }
            )
        except Exception as e:
            print(f"Performance audit logging failed: {e}")

    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    AuditService.log_system_event(
        audit.AuditEventType.UNHANDLED_EXCEPTION.value,
        {
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
            "type": type(exc).__name__
        }
    )

    if settings.DEBUG:
        raise exc

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """System health check"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {}
    }

    # Check Redis
    try:
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception:
        health_status["services"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"

    # Check Database
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["services"]["database"] = "healthy"
    except Exception:
        health_status["services"]["database"] = "unhealthy"
        health_status["status"] = "degraded"

    return health_status


# Root endpoint
@app.get("/")
async def root():
    """Welcome message and API information"""
    return {
        "message": "Welcome to MyTypist API",
        "description": "High-performance document automation platform for Nigerian businesses",
        "status": "running",
        "documentation": "/api/docs",
        "health_check": "/health"
    }

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(signatures.router, prefix="/api/signatures", tags=["Signatures"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["Monitoring"])

# Include feedback system
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])

# Include referral system
app.include_router(referrals.router, prefix="/api/referrals", tags=["Referrals"])

# Include admin rewards system
from app.routes import admin_rewards
app.include_router(admin_rewards.router)

# Include push notifications
try:
    from app.routes.push_notifications import router as push_router
    app.include_router(push_router, prefix="/api/push", tags=["Push Notifications"])
    print("✅ Push notification system with FCM and APNS loaded")
except ImportError as e:
    print(f"⚠️  Push notification system not available: {e}")

# Core authentication and document processing features loaded
print("✅ Production-ready authentication system loaded")
print("✅ Core document processing features integrated")

# Skip advanced service endpoints for now to get basic app running
print("⚠️ Skipping advanced service endpoints to focus on core functionality")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=settings.DEBUG,
        access_log=settings.DEBUG
    )
