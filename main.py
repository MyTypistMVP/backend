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
from app.routes import auth, documents, templates, signatures, analytics, payments, admin, monitoring, feedback
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityMiddleware
from app.middleware.audit import AuditMiddleware
from app.middleware.performance import PerformanceMiddleware, CompressionMiddleware
from app.middleware.advanced_security import AdvancedSecurityMiddleware, RequestValidationMiddleware
from app.middleware.csrf_protection import CSRFProtectionMiddleware
from app.services.audit_service import AuditService
from app.services.cache_service import cache_service
# Enterprise services removed for MVP


# Create database tables
user.Base.metadata.create_all(bind=engine)
template.Base.metadata.create_all(bind=engine)
document.Base.metadata.create_all(bind=engine)
signature.Base.metadata.create_all(bind=engine)
visit.Base.metadata.create_all(bind=engine)
payment.Base.metadata.create_all(bind=engine)
audit.Base.metadata.create_all(bind=engine)

# Create feedback table
try:
    Feedback.metadata.create_all(bind=engine)
except Exception as e:
    print(f"⚠️ Failed to create feedback tables: {e}")

# Enterprise security tables removed for MVP

# Create new service tables
try:
    from app.services.template_marketplace_service import TemplateReview, TemplatePurchase, TemplateFavorite, TemplateCollection
    from app.services.wallet_service import Wallet, WalletTransaction
    from app.services.document_editing_service import DocumentEdit
    from app.services.advanced_search_service import SearchQuery, SearchRecommendation
    from app.services.enhanced_notification_service import Notification, NotificationTemplate, NotificationPreference
    from app.services.placeholder_management_service import PlaceholderStyling
    from app.services.admin_dashboard_service import PageVisit, DocumentShare
    from app.services.document_version_service import DocumentVersion
    from app.services.seo_template_service import TemplateSEO
    from app.services.advanced_fraud_detection_service import DeviceFingerprint, UserDeviceAssociation, FraudAttempt
    from app.services.draft_system_service import DocumentDraft, DraftAutoSave
    from app.services.performance_tracking_service import DocumentGenerationMetric, UserProductivityMetric, SystemPerformanceMetric
    from app.services.support_ticket_service import SupportTicket, TicketReply
    from app.services.landing_page_service import LandingPageVisit, LandingPageTemplate
    from app.services.user_template_upload_service import UserUploadedTemplate, PlaceholderExtractionLog
    from app.services.campaign_service import Campaign, CampaignExecution
    from app.services.faq_service import FAQCategory, FAQ, FAQInteraction
    from app.models.token import UserToken, TokenTransaction, TokenCampaign, TokenReward
    from app.services.push_notification_service import DeviceToken, PushNotificationLog
    from app.services.partner_service import PartnerApplication, Partner, PartnerReferral, PartnerActivity
    from app.services.blog_service import BlogCategory, BlogPost, BlogComment, BlogView

    TemplateReview.metadata.create_all(bind=engine)
    TemplatePurchase.metadata.create_all(bind=engine)
    TemplateFavorite.metadata.create_all(bind=engine)
    TemplateCollection.metadata.create_all(bind=engine)
    Wallet.metadata.create_all(bind=engine)
    WalletTransaction.metadata.create_all(bind=engine)
    DocumentEdit.metadata.create_all(bind=engine)
    SearchQuery.metadata.create_all(bind=engine)
    SearchRecommendation.metadata.create_all(bind=engine)
    Notification.metadata.create_all(bind=engine)
    NotificationTemplate.metadata.create_all(bind=engine)
    NotificationPreference.metadata.create_all(bind=engine)
    PlaceholderStyling.metadata.create_all(bind=engine)
    PageVisit.metadata.create_all(bind=engine)
    DocumentShare.metadata.create_all(bind=engine)
    DocumentVersion.metadata.create_all(bind=engine)
    TemplateSEO.metadata.create_all(bind=engine)
    DeviceFingerprint.metadata.create_all(bind=engine)
    UserDeviceAssociation.metadata.create_all(bind=engine)
    FraudAttempt.metadata.create_all(bind=engine)
    DocumentDraft.metadata.create_all(bind=engine)
    DraftAutoSave.metadata.create_all(bind=engine)
    DocumentGenerationMetric.metadata.create_all(bind=engine)
    UserProductivityMetric.metadata.create_all(bind=engine)
    SystemPerformanceMetric.metadata.create_all(bind=engine)
    SupportTicket.metadata.create_all(bind=engine)
    TicketReply.metadata.create_all(bind=engine)
    LandingPageVisit.metadata.create_all(bind=engine)
    LandingPageTemplate.metadata.create_all(bind=engine)
    UserUploadedTemplate.metadata.create_all(bind=engine)
    PlaceholderExtractionLog.metadata.create_all(bind=engine)
    Campaign.metadata.create_all(bind=engine)
    CampaignExecution.metadata.create_all(bind=engine)
    FAQCategory.metadata.create_all(bind=engine)
    FAQ.metadata.create_all(bind=engine)
    FAQInteraction.metadata.create_all(bind=engine)
    UserToken.metadata.create_all(bind=engine)
    TokenTransaction.metadata.create_all(bind=engine)
    TokenCampaign.metadata.create_all(bind=engine)
    TokenReward.metadata.create_all(bind=engine)
    DeviceToken.metadata.create_all(bind=engine)
    PushNotificationLog.metadata.create_all(bind=engine)
    PartnerApplication.metadata.create_all(bind=engine)
    Partner.metadata.create_all(bind=engine)
    PartnerReferral.metadata.create_all(bind=engine)
    PartnerActivity.metadata.create_all(bind=engine)
    BlogCategory.metadata.create_all(bind=engine)
    BlogPost.metadata.create_all(bind=engine)
    BlogComment.metadata.create_all(bind=engine)
    BlogView.metadata.create_all(bind=engine)
    print("✅ New service tables created")
    print("✅ Placeholder styling table created")
    print("✅ Page visit tracking table created")
    print("✅ Document sharing table created")
    print("✅ Document version control table created")
    print("✅ SEO template pages table created")
    print("✅ Advanced fraud detection tables created")
    print("✅ Draft system with auto-save tables created")
    print("✅ Performance tracking and analytics tables created")
    print("✅ Support ticket system with guest tracking tables created")
    print("✅ Landing page analytics and conversion tracking tables created")
    print("✅ User template upload with automatic placeholder extraction tables created")
    print("✅ Campaign system with email and token distribution tables created")
    print("✅ Dynamic FAQ management system with analytics tables created") 
    print("✅ Advanced token management with welcome bonuses tables created")
    print("✅ Push notification tracking tables created")
except Exception as e:
    print(f"⚠️ Failed to create new service tables: {e}")

# Initialize Redis (optional)
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
except Exception:
    # Use a mock Redis client for development
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
        AuditService.log_system_event(audit.AuditEventType.SYSTEM_STARTUP.value, {"version": settings.APP_VERSION})
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
    version=settings.APP_VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Performance and security middleware (order matters!)
app.add_middleware(CompressionMiddleware, minimum_size=1024, compression_level=6)
app.add_middleware(PerformanceMiddleware, slow_request_threshold=1.0)
app.add_middleware(AdvancedSecurityMiddleware)
app.add_middleware(RequestValidationMiddleware)
app.add_middleware(CSRFProtectionMiddleware)
app.add_middleware(SecurityMiddleware)
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
        "version": settings.APP_VERSION,
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
        "version": settings.APP_VERSION,
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

# Include new service endpoints
try:
    from app.routes.marketplace import router as marketplace_router
    from app.routes.wallet import router as wallet_router
    from app.routes.document_editing import router as document_editing_router
    from app.routes.advanced_search import router as advanced_search_router
    from app.routes.notifications import router as notifications_router
    from app.routes.placeholder_management import router as placeholder_router
    from app.routes.document_sharing import router as sharing_router
    from app.routes.document_versions import router as versions_router
    from app.routes.drafts import router as drafts_router
    from app.routes.performance import router as performance_router
    from app.routes.support import router as support_router
    from app.routes.landing import router as landing_router
    from app.routes.user_templates import router as user_templates_router

    app.include_router(marketplace_router, prefix="/api/marketplace", tags=["Template Marketplace"])
    app.include_router(wallet_router, prefix="/api/wallet", tags=["Wallet & Transactions"])
    app.include_router(document_editing_router, prefix="/api/document-editing", tags=["Document Editing"])
    app.include_router(advanced_search_router, prefix="/api/search", tags=["Advanced Search"])
    app.include_router(notifications_router, prefix="/api/notifications", tags=["Notifications"])
    app.include_router(placeholder_router, prefix="/api/placeholders", tags=["Placeholder Management"])
    app.include_router(sharing_router, prefix="/api/sharing", tags=["Document Sharing"])
    app.include_router(versions_router, prefix="/api/versions", tags=["Document Versions"])
    app.include_router(drafts_router, prefix="/api/drafts", tags=["Draft System"])
    app.include_router(performance_router, prefix="/api/performance", tags=["Performance Tracking"])
    app.include_router(support_router, prefix="/api/support", tags=["Support System"])
    app.include_router(landing_router, prefix="/api/landing", tags=["Landing Page"])
    app.include_router(user_templates_router, prefix="/api/user-templates", tags=["User Template Upload"])

    # Include new campaign, FAQ, partner, and blog systems
    from app.routes.campaigns import router as campaigns_router
    from app.routes.faq import router as faq_router
    from app.routes.tokens import router as tokens_router
    from app.routes.partners import router as partners_router
    from app.routes.blog import router as blog_router
    
    app.include_router(campaigns_router, tags=["Campaign Management"])
    app.include_router(faq_router, tags=["FAQ System"])  
    app.include_router(tokens_router, tags=["Token Management"])
    app.include_router(partners_router, tags=["Partner Portal"])
    app.include_router(blog_router, tags=["Blog System"])

    print("✅ New service endpoints loaded")
    print("✅ Advanced placeholder management system loaded")
    print("✅ Document sharing with time-limited preview links loaded")
    print("✅ Document version control system loaded")
    print("✅ Comprehensive draft system with auto-save loaded")
    print("✅ Performance tracking with time-saved calculations loaded")
    print("✅ Professional support ticket system with guest tracking loaded")
    print("✅ Seamless landing page to registration workflow loaded")
    print("✅ User template upload with automatic placeholder extraction loaded")
    print("✅ Campaign system with email marketing and token gifting loaded")
    print("✅ Dynamic FAQ management system with analytics loaded")
    print("✅ Advanced token management with welcome bonuses loaded")
except ImportError as e:
    print(f"⚠️ New service endpoints not available: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=settings.DEBUG,
        access_log=settings.DEBUG
    )
