# MyTypist Backend Deployment Guide

## System Requirements

### Core Dependencies
- **Python**: 3.11+ (Required)
- **PostgreSQL**: 13+ (Primary database)
- **Redis**: 6+ (Caching and task queue)

### System Packages (Ubuntu/Debian)
```bash
# Essential packages
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip
sudo apt install -y postgresql-client redis-tools
sudo apt install -y build-essential libpq-dev

# Document processing dependencies
sudo apt install -y tesseract-ocr
sudo apt install -y poppler-utils
sudo apt install -y libmagic1
```

## Quick Deployment

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd mytypist-backend
python3.11 -m venv venv
source venv/bin/activate
pip install uv
uv sync
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your actual values
nano .env
```

### 3. Database Setup
```bash
# Run database migrations
alembic upgrade head
```

### 4. Start Services
```bash
# Development
uvicorn main:app --host 0.0.0.0 --port 5000 --reload

# Production
gunicorn --conf gunicorn.conf.py main:app
```

## Production Deployment

### Environment Variables (Required)
```bash
# Core Settings
SECRET_KEY=your-32-char-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379

# Payment Gateway
FLUTTERWAVE_PUBLIC_KEY=your-public-key
FLUTTERWAVE_SECRET_KEY=your-secret-key

# Email Service
SENDGRID_API_KEY=your-sendgrid-key
```

### Security Checklist
- [ ] Set strong SECRET_KEY (32+ characters)
- [ ] Configure proper ALLOWED_HOSTS and ALLOWED_ORIGINS
- [ ] Set DEBUG=false in production
- [ ] Use HTTPS for all external connections
- [ ] Configure firewall rules
- [ ] Set up SSL/TLS certificates

### Database Migration
```bash
# Always run migrations on deployment
alembic upgrade head
```

### Performance Optimization
- Configure database connection pooling
- Set up Redis for caching
- Use Gunicorn with uvloop workers
- Enable gzip compression
- Configure proper log rotation

## Health Monitoring

### Health Check Endpoints
- `GET /health` - System health status
- `GET /` - API information

### Expected Response
```json
{
  "status": "healthy",
  "services": {
    "redis": "healthy",
    "database": "healthy"
  }
}
```

## Troubleshooting

### Common Issues
1. **Database connection failed**: Check DATABASE_URL and PostgreSQL status
2. **Redis connection failed**: Verify Redis server is running
3. **Import errors**: Run `uv sync` to install dependencies
4. **Migration errors**: Check database permissions and run `alembic upgrade head`

### Log Locations
- Application: stdout/stderr
- Database: PostgreSQL logs
- Redis: Redis logs
- Gunicorn: Access and error logs

## Scaling Considerations

### Horizontal Scaling
- Use load balancer (Nginx/HAProxy)
- Configure session storage in Redis
- Set up database read replicas
- Use CDN for static assets

### Monitoring
- Set up error tracking (Sentry)
- Monitor database performance
- Track API response times
- Set up alerts for critical errors