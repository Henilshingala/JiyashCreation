#!/usr/bin/env python3
"""
Quick setup script for JiyashCreation Django project
"""
import os
import sys
import subprocess
import secrets
import string

def generate_secret_key():
    """Generate a secure Django SECRET_KEY"""
    chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(50))

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_path = '.env'
    if os.path.exists(env_path):
        print("✅ .env file already exists")
        return
    
    print("📝 Creating .env file...")
    secret_key = generate_secret_key()
    
    env_content = f"""# Django Settings
SECRET_KEY={secret_key}
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for production, consider PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost:5432/jiyash_db

# Email Settings (for password reset functionality)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# JWT Settings (optional - will use SECRET_KEY if not set)
# JWT_SECRET_KEY=your-jwt-secret-key

# Security Settings (for production)
# SECURE_SSL_REDIRECT=True
# SECURE_PROXY_SSL_HEADER=HTTP_X_FORWARDED_PROTO,https

# Static/Media Files (for production)
# STATIC_ROOT=/path/to/static/files
# MEDIA_ROOT=/path/to/media/files"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created with secure SECRET_KEY")

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 JiyashCreation Django Project Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: manage.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing dependencies"):
        print("⚠️  Warning: Could not install dependencies. Please run 'pip install -r requirements.txt' manually.")
    
    # Run migrations
    run_command("python manage.py makemigrations", "Creating migrations")
    run_command("python manage.py migrate", "Applying migrations")
    
    # Collect static files
    run_command("python manage.py collectstatic --noinput", "Collecting static files")
    
    # Run security check (use simple version for Windows compatibility)
    run_command("python manage.py security_check_simple", "Running security check")
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Create a superuser: python manage.py createsuperuser")
    print("2. Start the development server: python manage.py runserver")
    print("3. Visit http://127.0.0.1:8000/ to see your site")
    print("4. Visit http://127.0.0.1:8000/admin/ for admin panel")
    print("\n🔒 For production deployment:")
    print("1. Review DEPLOYMENT_CHECKLIST.md")
    print("2. Set DEBUG=False in .env")
    print("3. Configure a production database")
    print("4. Set up SSL/HTTPS")
    print("=" * 50)

if __name__ == "__main__":
    main()
