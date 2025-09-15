#!/usr/bin/env python3
"""
MyTypist Backend Deployment Verification Script
Run this script before deploying to ensure all systems are ready
"""

import os
import sys
import requests
import redis
import psycopg2
from datetime import datetime


def check_python_version():
    """Verify Python version is 3.11+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Required: Python 3.11+")
        return False


def check_environment_variables():
    """Check required environment variables"""
    required_vars = [
        'DATABASE_URL',
        'SECRET_KEY',
        'JWT_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ Required environment variables - OK")
        return True


def check_database_connection():
    """Test PostgreSQL database connection"""
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL not set")
            return False
            
        # Parse connection URL for psycopg2
        import urllib.parse
        result = urllib.parse.urlparse(database_url)
        
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        
        print("✅ Database connection - OK")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def check_redis_connection():
    """Test Redis connection"""
    try:
        redis_host = os.getenv('REDIS_HOST', 'localhost')
        redis_port = int(os.getenv('REDIS_PORT', '6000'))  # Fixed: MyTypist uses port 6000
        redis_password = os.getenv('REDIS_PASSWORD', None)
        
        r = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password if redis_password else None,
            decode_responses=True,
            socket_connect_timeout=5
        )
        
        r.ping()
        print("✅ Redis connection - OK")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False


def check_api_endpoints():
    """Test API endpoints"""
    base_url = "http://localhost:5000"
    
    endpoints = [
        "/",
        "/health"
    ]
    
    all_ok = True
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK (Status: {response.status_code})")
            else:
                print(f"❌ {endpoint} - Failed (Status: {response.status_code})")
                all_ok = False
        except Exception as e:
            print(f"❌ {endpoint} - Connection failed: {e}")
            all_ok = False
    
    return all_ok


def check_file_permissions():
    """Check file system permissions"""
    storage_path = os.getenv('STORAGE_PATH', './storage')
    
    try:
        # Check if storage directories exist and are writable
        os.makedirs(storage_path, exist_ok=True)
        test_file = os.path.join(storage_path, 'test_write.tmp')
        
        with open(test_file, 'w') as f:
            f.write('test')
        
        os.remove(test_file)
        print("✅ File system permissions - OK")
        return True
        
    except Exception as e:
        print(f"❌ File system permissions failed: {e}")
        return False


def main():
    """Run all deployment checks"""
    print("🔍 MyTypist Backend Deployment Verification")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Environment Variables", check_environment_variables),
        ("Database Connection", check_database_connection),
        ("Redis Connection", check_redis_connection),
        ("API Endpoints", check_api_endpoints),
        ("File Permissions", check_file_permissions)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"Checking {name}...")
        if check_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🚀 DEPLOYMENT READY - All checks passed!")
        return 0
    else:
        print("❌ DEPLOYMENT NOT READY - Please fix the issues above")
        return 1


if __name__ == "__main__":
    sys.exit(main())