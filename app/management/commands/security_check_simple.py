"""
Simple Django management command to perform security checks (ASCII only)
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from app.models import User
import os


class Command(BaseCommand):
    help = 'Perform security checks on the Django application (ASCII version)'

    def handle(self, *args, **options):
        self.stdout.write('Starting security check...\n')
        
        issues_found = []
        
        # Check 1: DEBUG setting
        if settings.DEBUG:
            issues_found.append("ERROR: DEBUG is set to True - should be False in production")
        else:
            self.stdout.write("OK: DEBUG is properly set to False")
        
        # Check 2: SECRET_KEY
        try:
            secret_key = settings.SECRET_KEY
            if not secret_key:
                issues_found.append("ERROR: SECRET_KEY is not set")
            elif len(secret_key) < 50:
                issues_found.append("ERROR: SECRET_KEY is too short (should be at least 50 characters)")
            elif 'django-insecure' in secret_key:
                issues_found.append("ERROR: SECRET_KEY appears to be a default Django key")
            else:
                self.stdout.write("OK: SECRET_KEY is properly configured")
        except AttributeError:
            issues_found.append("ERROR: SECRET_KEY is not configured")
        
        # Check 3: ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or settings.ALLOWED_HOSTS == ['*']:
            issues_found.append("ERROR: ALLOWED_HOSTS is not properly configured")
        else:
            self.stdout.write("OK: ALLOWED_HOSTS is configured")
        
        # Check 4: Security middleware
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]
        
        for middleware in required_middleware:
            if middleware in settings.MIDDLEWARE:
                self.stdout.write(f"OK: {middleware} is enabled")
            else:
                issues_found.append(f"ERROR: {middleware} is missing from MIDDLEWARE")
        
        # Check 5: Security headers
        security_settings = [
            ('SECURE_BROWSER_XSS_FILTER', True),
            ('SECURE_CONTENT_TYPE_NOSNIFF', True),
            ('X_FRAME_OPTIONS', 'DENY'),
        ]
        
        for setting_name, expected_value in security_settings:
            if hasattr(settings, setting_name):
                actual_value = getattr(settings, setting_name)
                if actual_value == expected_value:
                    self.stdout.write(f"OK: {setting_name} is properly configured")
                else:
                    issues_found.append(f"ERROR: {setting_name} is set to {actual_value}, should be {expected_value}")
            else:
                issues_found.append(f"ERROR: {setting_name} is not configured")
        
        # Check 6: Database configuration
        if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
            if settings.DEBUG:
                self.stdout.write("WARNING: Using SQLite database (OK for development)")
            else:
                issues_found.append("ERROR: Using SQLite in production - consider PostgreSQL or MySQL")
        else:
            self.stdout.write("OK: Using production-ready database")
        
        # Summary
        self.stdout.write(f"\n{'='*50}")
        if issues_found:
            self.stdout.write(f'Found {len(issues_found)} security issues:')
            for issue in issues_found:
                self.stdout.write(f"  {issue}")
            
            self.stdout.write(f"\nRecommendations:")
            self.stdout.write("1. Set DEBUG=False in production")
            self.stdout.write("2. Use environment variables for sensitive settings")
            self.stdout.write("3. Use a production database (PostgreSQL/MySQL)")
            self.stdout.write("4. Enable all security middleware")
            self.stdout.write("5. Set proper file permissions")
            self.stdout.write("6. Use HTTPS in production")
            
        else:
            self.stdout.write('No major security issues found!')
        
        self.stdout.write(f"{'='*50}")
        self.stdout.write("Security check completed.")
