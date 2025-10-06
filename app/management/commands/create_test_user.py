"""
Django management command to create a test user
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from app.models import User


class Command(BaseCommand):
    help = 'Create a test user for login testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='test@jiyash.com',
            help='Email for the test user',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='testpass123',
            help='Password for the test user',
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(f"User with email {email} already exists")
            
            # Update the existing user's password
            user = User.objects.get(email=email)
            user.password = make_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"Updated password for existing user: {email}")
            )
        else:
            # Create new user
            user = User.objects.create(
                first_name='Test',
                last_name='User',
                email=email,
                password=make_password(password),
                confirm_password=make_password(password),
                country='India'
            )
            self.stdout.write(
                self.style.SUCCESS(f"Created test user: {email}")
            )
        
        self.stdout.write(f"Login credentials:")
        self.stdout.write(f"Email: {email}")
        self.stdout.write(f"Password: {password}")
        self.stdout.write(f"URL: http://127.0.0.1:8002/login/")
