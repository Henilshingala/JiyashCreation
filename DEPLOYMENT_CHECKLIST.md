# Django Deployment Security Checklist

## Pre-Deployment Security Checklist

### ✅ Environment Configuration
- [ ] Set `DEBUG=False` in production
- [ ] Configure strong `SECRET_KEY` (50+ characters)
- [ ] Set proper `ALLOWED_HOSTS`
- [ ] Use environment variables for sensitive data
- [ ] Create `.env` file from `.env.example`

### ✅ Database Security
- [ ] Use PostgreSQL or MySQL in production (not SQLite)
- [ ] Configure database connection with SSL
- [ ] Set up database backups
- [ ] Use strong database passwords
- [ ] Limit database user permissions

### ✅ Security Headers & Middleware
- [ ] Enable `SecurityMiddleware`
- [ ] Enable `CsrfViewMiddleware`
- [ ] Enable `XFrameOptionsMiddleware`
- [ ] Set `SECURE_BROWSER_XSS_FILTER=True`
- [ ] Set `SECURE_CONTENT_TYPE_NOSNIFF=True`
- [ ] Set `X_FRAME_OPTIONS='DENY'`

### ✅ HTTPS Configuration
- [ ] Obtain SSL certificate
- [ ] Set `SECURE_SSL_REDIRECT=True`
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Set `CSRF_COOKIE_SECURE=True`
- [ ] Configure `SECURE_HSTS_SECONDS`

### ✅ Authentication & Authorization
- [ ] Review user permissions
- [ ] Ensure strong admin passwords
- [ ] Enable two-factor authentication for admin
- [ ] Review JWT token expiration settings
- [ ] Implement rate limiting for login attempts

### ✅ File Security
- [ ] Set proper file permissions (644 for files, 755 for directories)
- [ ] Secure media file uploads
- [ ] Configure static file serving
- [ ] Remove debug files and logs from production

### ✅ Logging & Monitoring
- [ ] Configure production logging
- [ ] Set up error monitoring (Sentry)
- [ ] Monitor failed login attempts
- [ ] Set up performance monitoring
- [ ] Configure log rotation

### ✅ Dependencies & Updates
- [ ] Update all dependencies to latest secure versions
- [ ] Remove development dependencies from production
- [ ] Set up automated security updates
- [ ] Regular dependency audits

## Deployment Commands

### 1. Run Security Check
```bash
python manage.py security_check
```

### 2. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Create Superuser
```bash
python manage.py createsuperuser
```

### 5. Test Deployment
```bash
python manage.py check --deploy
```

## Server Configuration

### Nginx Configuration (Example)
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    location /static/ {
        alias /path/to/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /path/to/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Gunicorn Configuration (gunicorn.conf.py)
```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

## Post-Deployment Verification

### ✅ Security Tests
- [ ] Test HTTPS redirect
- [ ] Verify security headers
- [ ] Test authentication flows
- [ ] Check for information disclosure
- [ ] Verify CSRF protection
- [ ] Test file upload security

### ✅ Functionality Tests
- [ ] Test all user flows
- [ ] Verify cart functionality
- [ ] Test wishlist operations
- [ ] Check payment integration
- [ ] Verify email functionality
- [ ] Test admin interface

### ✅ Performance Tests
- [ ] Load testing
- [ ] Database query optimization
- [ ] Static file loading
- [ ] Image optimization
- [ ] CDN configuration

## Monitoring & Maintenance

### Daily
- [ ] Check error logs
- [ ] Monitor failed login attempts
- [ ] Review security alerts

### Weekly
- [ ] Database backup verification
- [ ] Security scan
- [ ] Performance metrics review

### Monthly
- [ ] Dependency updates
- [ ] Security patches
- [ ] Log rotation
- [ ] Backup testing

## Emergency Procedures

### Security Incident Response
1. Identify and contain the threat
2. Change all passwords and tokens
3. Review access logs
4. Patch vulnerabilities
5. Notify users if necessary
6. Document the incident

### Backup Recovery
1. Stop the application
2. Restore database from backup
3. Restore media files
4. Verify data integrity
5. Restart application
6. Test functionality

## Contact Information

- **Security Team**: security@jiyashcreation.com
- **DevOps Team**: devops@jiyashcreation.com
- **Emergency Contact**: +1-XXX-XXX-XXXX
