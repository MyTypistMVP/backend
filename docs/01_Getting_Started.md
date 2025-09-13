# MyTypist Backend - Getting Started Guide

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Environment Setup](#environment-setup)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Configuration Reference](#configuration-reference)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Overview

MyTypist is a production-ready, high-performance SaaS document automation platform designed specifically for Nigerian businesses. Built with FastAPI, PostgreSQL, Redis, and Flutterwave integration, it delivers lightning-fast document generation with enterprise-grade security and scalability.

### Key Features
- **🚄 Lightning Fast**: Sub-500ms document generation for up to 5 documents
- **🔒 Enterprise Security**: Multi-layered security with encryption, audit trails, and threat detection
- **💳 Payment Ready**: Complete Flutterwave integration for Nigerian businesses
- **📊 Production Monitoring**: Real-time performance monitoring and alerting
- **🔄 Auto-scaling**: Optimized for horizontal and vertical scaling
- **📝 Complete Documentation**: Comprehensive guides for all aspects

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend App  │    │     Nginx       │    │  FastAPI App    │
│  (React/Vue/    │◄──►│ Load Balancer   │◄──►│   (Gunicorn +   │
│   Angular)      │    │   + SSL/TLS     │    │   Uvicorn)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │     Redis       │◄────────────┤
                       │   (Caching +    │             │
                       │  Task Queue)    │             │
                       └─────────────────┘             │
                                                        │
                       ┌─────────────────┐             │
                       │   PostgreSQL    │◄────────────┘
                       │   (Primary DB   │
                       │  + Backups)     │
                       └─────────────────┘
```

---

## Quick Start

### Development Setup (5 minutes)
```bash
# 1. Clone and setup
git clone <repository-url>
cd mytypist-backend
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.template .env.development
# Edit .env.development with your configuration

# 4. Initialize database
python scripts/setup_database.py

# 5. Start development server
python main.py
```

Your development server will be running at: `http://localhost:5000`

### Verify Installation
```bash
# Check health endpoint
curl http://localhost:5000/health

# Expected response:
{
  "status": "healthy",
  "service": "MyTypist Backend",
  "version": "1.0.0"
}
```

---

## Environment Setup

### System Requirements

#### Development
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.11+ (recommended 3.11)
- **RAM**: Minimum 4GB, recommended 8GB
- **Storage**: 2GB free space for development

#### Production
- **OS**: Ubuntu 20.04+ LTS (recommended)
- **CPU**: Minimum 2 cores, recommended 4+ cores
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Minimum 20GB SSD for optimal performance

### Required Services

#### Development
- **Database**: PostgreSQL (required)
- **Cache**: Optional Redis or in-memory caching

#### Production
- **Database**: PostgreSQL 15+ (required)
- **Cache**: Redis 7+ (required)
- **Web Server**: Nginx (recommended)
- **SSL**: Let's Encrypt or commercial certificate

---

## Development Setup

### 1. Python Environment Setup

#### Install Python 3.11
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# macOS with Homebrew
brew install python@3.11

# Windows
# Download from python.org or use winget
winget install Python.Python.3.11
```

#### Create Virtual Environment
```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Verify Python version
python --version  # Should show Python 3.11.x
```

### 2. Install Dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
pip list | grep sqlalchemy
pip list | grep redis
```

### 3. Environment Configuration

Create `.env.development` file:
```env
# Environment Configuration
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-not-for-production-use-only

# Application Settings
APP_NAME=MyTypist Backend
API_PREFIX=/api
TIMEZONE=Africa/Lagos

# Database (Postgres for development)

# Redis (optional for development)
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=false

# JWT Configuration
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_SECRET_KEY=dev-jwt-secret-key

# File Storage
STORAGE_PATH=./storage
TEMPLATES_PATH=./storage/templates
DOCUMENTS_PATH=./storage/documents
UPLOADS_PATH=./storage/uploads
MAX_FILE_SIZE=104857600  # 100MB

# Development Payment (Test Mode)
FLUTTERWAVE_PUBLIC_KEY=FLWPUBK_TEST-your-test-key
FLUTTERWAVE_SECRET_KEY=FLWSECK_TEST-your-test-key

# Development Email (optional)
SENDGRID_API_KEY=your-test-sendgrid-key
FROM_EMAIL=dev@mytypist.com

# CORS (allow localhost)
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Performance (development)
WORKERS=1
SLOW_REQUEST_THRESHOLD=5.0
CACHE_TTL=60
```

### 4. Database Setup

#### Automated Setup
```bash
# Run database setup script
python scripts/setup_database.py

# This script will:
# - Create all database tables
# - Create sample admin user
# - Add sample templates (optional)
```

#### Manual Database Setup
```python
# Alternative: Manual setup
from database import DatabaseManager
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

# Create tables
DatabaseManager.create_all_tables()

# Create admin user
admin_user = User(
    email="admin@mytypist.com",
    full_name="System Administrator",
    role=UserRole.ADMIN,
    is_active=True,
    email_verified=True
)
admin_user.hashed_password = AuthService.hash_password("admin123")
# Save to database...
```

### 5. Directory Structure Setup
```bash
# Create required directories
mkdir -p storage/{templates,documents,signatures,uploads,quarantine}
mkdir -p logs
mkdir -p backups

# Set permissions (Linux/macOS)
chmod 755 storage
chmod 750 storage/quarantine

echo "✅ Development environment setup complete!"
```

### 6. Start Development Server
```bash
# Start the development server
python main.py

# Or use uvicorn directly
uvicorn main:app --host 127.0.0.1 --port 5000 --reload

# Server will start at: http://localhost:5000
```

### 7. Verify Development Setup
```bash
# Test API health
curl http://localhost:5000/health

# Test authentication
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@mytypist.com","password":"admin123"}'

# Access API documentation
# Open in browser: http://localhost:5000/docs
```

---

## Production Deployment

### 1. Server Preparation

#### System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install Redis
sudo apt install redis-server

# Install Nginx
sudo apt install nginx

# Install system dependencies
sudo apt install build-essential libpq-dev python3-magic git curl
```

#### Application Deployment
```bash
# Clone repository
git clone <repository-url>
cd mytypist-backend

# Create production user
sudo useradd -m -s /bin/bash mytypist
sudo usermod -aG www-data mytypist

# Move to production directory
sudo mv mytypist-backend /var/www/
sudo chown -R mytypist:mytypist /var/www/mytypist-backend

# Switch to production user
sudo -u mytypist -i
cd /var/www/mytypist-backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

#### PostgreSQL Configuration
```bash
# Switch to postgres user
sudo -u postgres psql

# Create production database and user
CREATE DATABASE mytypist_prod;
CREATE USER mytypist_user WITH PASSWORD 'secure_production_password';
GRANT ALL PRIVILEGES ON DATABASE mytypist_prod TO mytypist_user;
ALTER USER mytypist_user CREATEDB;
ALTER DATABASE mytypist_prod OWNER TO mytypist_user;
\q
```

#### Production Database Optimization
Edit `/etc/postgresql/15/main/postgresql.conf`:
```conf
# Memory settings (adjust based on available RAM)
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 200
superuser_reserved_connections = 3

# Performance settings
wal_level = replica
checkpoint_completion_target = 0.9
random_page_cost = 1.1
effective_io_concurrency = 200

# Logging
log_min_duration_statement = 1000
log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h '
```

### 3. Production Environment Configuration

Create `.env.production`:
```env
# Environment Configuration
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-ultra-secure-production-secret-key-minimum-32-chars

# Application Settings
APP_NAME=MyTypist Backend
API_PREFIX=/api
TIMEZONE=Africa/Lagos

# Database (PostgreSQL)
DATABASE_URL=postgresql://mytypist_user:secure_production_password@localhost:5432/mytypist_prod
DB_POOL_SIZE=25
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true
REDIS_MAX_CONNECTIONS=25

# JWT Configuration
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_SECRET_KEY=your-different-jwt-secret-key

# Encryption
ENCRYPTION_KEY=your-256-bit-base64-encoded-encryption-key
ENCRYPTION_ENABLED=true

# File Storage
STORAGE_PATH=/var/mytypist/storage
TEMPLATES_PATH=/var/mytypist/storage/templates
DOCUMENTS_PATH=/var/mytypist/storage/documents
UPLOADS_PATH=/var/mytypist/storage/uploads
MAX_FILE_SIZE=104857600

# Production Payment (Live Keys)
FLUTTERWAVE_PUBLIC_KEY=FLWPUBK-your-live-public-key
FLUTTERWAVE_SECRET_KEY=FLWSECK-your-live-secret-key
FLUTTERWAVE_WEBHOOK_SECRET=your-webhook-verification-hash

# Email Configuration
SENDGRID_API_KEY=your-production-sendgrid-key
FROM_EMAIL=noreply@mytypist.com
FROM_NAME=MyTypist

# CORS (restrict to your domains)
ALLOWED_ORIGINS=["https://mytypist.net", "https://app.mytypist.net"]
ALLOWED_HOSTS=["mytypist.net", "api.mytypist.net"]

# Performance Settings
WORKERS=4
MAX_CONCURRENT_UPLOADS=10
SLOW_REQUEST_THRESHOLD=0.5
COMPRESSION_LEVEL=6
CACHE_TTL=3600
TEMPLATE_CACHE_TTL=86400

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
AUTH_RATE_LIMIT=5
UPLOAD_RATE_LIMIT=10

# Monitoring
SENTRY_DSN=your-sentry-dsn-for-error-tracking
SENTRY_ENVIRONMENT=production
LOG_LEVEL=INFO
MONITORING_ENABLED=true
```

### 4. Application Service Setup

Create systemd service `/etc/systemd/system/mytypist-backend.service`:
```ini
[Unit]
Description=MyTypist Backend API
After=network.target postgresql.service redis.service

[Service]
Type=forking
User=mytypist
Group=mytypist
WorkingDirectory=/var/www/mytypist-backend
Environment=PATH=/var/www/mytypist-backend/venv/bin
ExecStart=/var/www/mytypist-backend/venv/bin/gunicorn main:app -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/mytypist`:
```nginx
upstream mytypist_backend {
    least_conn;
    server 127.0.0.1:5000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;

server {
    listen 443 ssl http2;
    server_name api.mytypist.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.mytypist.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.mytypist.net/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    client_max_body_size 100M;

    location /api/auth/ {
        limit_req zone=auth burst=10 nodelay;
        proxy_pass http://mytypist_backend;
        include /etc/nginx/proxy_params;
    }

    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://mytypist_backend;
        include /etc/nginx/proxy_params;
    }

    location /health {
        proxy_pass http://mytypist_backend;
        include /etc/nginx/proxy_params;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.mytypist.net;
    return 301 https://$server_name$request_uri;
}
```

### 6. SSL Certificate Setup
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d api.mytypist.net

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 7. Start Services
```bash
# Enable and start database
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Enable and start application
sudo systemctl enable mytypist-backend
sudo systemctl start mytypist-backend

# Enable and start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Check service status
sudo systemctl status mytypist-backend
sudo systemctl status postgresql
sudo systemctl status redis-server
sudo systemctl status nginx
```

### 8. Database Migration
```bash
# Switch to application user
sudo -u mytypist -i
cd /var/www/mytypist-backend
source venv/bin/activate

# Run database migrations
python -m alembic upgrade head

# Create initial admin user
python scripts/create_admin.py
```

### 9. Verify Production Deployment
```bash
# Test HTTPS endpoint
curl https://api.mytypist.com/health

# Test API functionality
curl -X POST https://api.mytypist.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@mytypist.net","password":"your_admin_password"}'

# Check SSL configuration
curl -I https://api.mytypist.net/
```

---

## Configuration Reference

### Environment Variables

#### Core Application
```env
ENVIRONMENT=development|staging|production
DEBUG=true|false
SECRET_KEY=your-cryptographically-secure-secret-key
APP_NAME=MyTypist Backend
API_PREFIX=/api
TIMEZONE=Africa/Lagos
```

#### Database Settings
```env
# PostgreSQL (Production)
DATABASE_URL=postgresql://user:pass@host:port/db
DB_POOL_SIZE=25
DB_MAX_OVERFLOW=35
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

```

#### Security Configuration
```env
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
JWT_SECRET_KEY=your-jwt-secret
ENCRYPTION_KEY=your-256-bit-key
ENCRYPTION_ENABLED=true
```

#### Performance Settings
```env
WORKERS=4
MAX_CONCURRENT_UPLOADS=10
SLOW_REQUEST_THRESHOLD=0.5
CACHE_TTL=3600
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Directory Structure
```
mytypist-backend/
├── app/                    # Application code
│   ├── routes/            # API endpoints
│   ├── services/          # Business logic
│   ├── models/            # Database models
│   ├── middleware/        # Custom middleware
│   └── utils/             # Utility functions
├── storage/               # File storage
│   ├── templates/         # Document templates
│   ├── documents/         # Generated documents
│   ├── signatures/        # Digital signatures
│   ├── uploads/          # User uploads
│   └── quarantine/       # Quarantined files
├── logs/                 # Application logs
├── scripts/              # Deployment scripts
├── tests/                # Test files
├── alembic/              # Database migrations
├── requirements.txt      # Python dependencies
├── main.py              # Application entry point
├── database.py          # Database configuration
├── config.py            # Application configuration
└── gunicorn.conf.py     # Production server config
```

---

## Troubleshooting

### Common Development Issues

#### 1. Python Version Issues
```bash
# Error: Python 3.11 not found
# Solution: Install Python 3.11
sudo apt install python3.11 python3.11-venv

# Verify installation
python3.11 --version
```

#### 2. Virtual Environment Issues
```bash
# Error: venv not activating
# Solution: Recreate virtual environment
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
```

#### 3. Database Connection Issues
```bash
# Error: Database not found
# Solution: Run database setup
python scripts/setup_database.py

# Or manually create tables
python -c "from database import DatabaseManager; DatabaseManager.create_all_tables()"
```

#### 4. Permission Issues (Linux/macOS)
```bash
# Error: Permission denied
# Solution: Fix file permissions
chmod +x scripts/*.py
chmod 755 storage
mkdir -p logs && chmod 755 logs
```

#### 5. Port Already in Use
```bash
# Error: Port 5000 in use
# Solution: Find and kill process
lsof -ti:5000 | xargs kill -9

# Or use different port
export PORT=5001
python main.py
```

### Common Production Issues

#### 1. Service Won't Start
```bash
# Check service logs
sudo journalctl -u mytypist-backend -f

# Check application logs
tail -f /var/log/mytypist/app.log

# Verify configuration
sudo -u mytypist -i
cd /var/www/mytypist-backend
source venv/bin/activate
python -c "from config import settings; print(settings)"
```

#### 2. Database Connection Failed
```bash
# Test database connection
sudo -u postgres psql -d mytypist_prod -c "SELECT version();"

# Check PostgreSQL status
sudo systemctl status postgresql

# Review database logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

#### 3. SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew --dry-run

# Test SSL configuration
curl -I https://api.mytypist. net/
```

#### 4. High Memory Usage
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Restart application
sudo systemctl restart mytypist-backend

# Optimize configuration
# Reduce DB_POOL_SIZE and WORKERS in .env
```

#### 5. Nginx Configuration Issues
```bash
# Test Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Reload Nginx
sudo systemctl reload nginx
```

### Getting Help

#### Log Locations
- **Application**: `/var/log/mytypist/app.log`
- **Security**: `/var/log/mytypist/security.log`
- **Access**: `/var/log/nginx/access.log`
- **Errors**: `/var/log/nginx/error.log`
- **System**: `journalctl -u mytypist-backend`

#### Health Check Endpoints
- **Basic Health**: `GET /health`
- **Detailed Health**: `GET /api/monitoring/health/detailed`
- **Performance Stats**: `GET /api/monitoring/performance/stats`

#### Support Channels
- **Documentation**: [API Reference Guide](02_API_Reference.md)
- **Integration**: [Integration Guide](03_Integration_Guide.md)
- **Security**: [Security & Performance Guide](04_Security_Performance.md)

---

## Next Steps

### After Development Setup
1. **Explore API Documentation**: Visit `http://localhost:5000/docs`
2. **Read API Reference**: [02_API_Reference.md](02_API_Reference.md)
3. **Learn Integration**: [03_Integration_Guide.md](03_Integration_Guide.md)
4. **Test Features**: Create templates, generate documents
5. **Setup Frontend**: Integrate with your frontend application

### After Production Deployment
1. **Setup Monitoring**: Configure performance monitoring
2. **Enable Backups**: Setup automated database backups
3. **Security Review**: Review [04_Security_Performance.md](04_Security_Performance.md)
4. **Load Testing**: Test with expected user load
5. **Team Training**: Train your team on new features

### Recommended Reading Order
1. **[Getting Started](01_Getting_Started.md)** ← You are here
2. **[API Reference](02_API_Reference.md)** - Complete API documentation
3. **[Integration Guide](03_Integration_Guide.md)** - Frontend integration
4. **[Security & Performance](04_Security_Performance.md)** - Security hardening
5. **[Development & Deployment](05_Development_Deployment.md)** - Advanced deployment
6. **[Monitoring & Maintenance](06_Monitoring_Maintenance.md)** - Operations guide
7. **[Architecture Guide](07_Architecture_Guide.md)** - System architecture

---

**Documentation Version**: 1.0  
**Last Updated**: January 2025  
**Status**: Production Ready ✅