#!/usr/bin/env python
"""
Setup script to create default country multipliers.
Run this script to set up the country multipliers in your database.

Usage:
python setup_country_multipliers.py
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jiyash.settings')
django.setup()

from app.models import CountryMultiplier
from decimal import Decimal

def setup_country_multipliers():
    """Set up default country multipliers"""
    
    # Create or update India multiplier
    india_multiplier, created = CountryMultiplier.objects.get_or_create(
        country_name='India',
        defaults={'multiplier': Decimal('1.0')}
    )
    
    if created:
        print(f"✅ Created India multiplier: {india_multiplier}")
    else:
        print(f"ℹ️  India multiplier already exists: {india_multiplier}")
    
    # Create or update Others multiplier
    others_multiplier, created = CountryMultiplier.objects.get_or_create(
        country_name='Others',
        defaults={'multiplier': Decimal('1.5')}  # 50% markup for other countries
    )
    
    if created:
        print(f"✅ Created Others multiplier: {others_multiplier}")
    else:
        print(f"ℹ️  Others multiplier already exists: {others_multiplier}")
    
    print("\n🎉 Country multipliers setup complete!")
    print("\n📝 To modify multipliers:")
    print("1. Go to Django Admin (/admin/)")
    print("2. Navigate to 'Country Multipliers'")
    print("3. Edit the multiplier values as needed")
    print("\n💡 How it works:")
    print("- Indian users see prices × India multiplier")
    print("- All other countries see prices × Others multiplier")
    print("- Prices are automatically calculated based on user's country")

if __name__ == '__main__':
    try:
        setup_country_multipliers()
    except Exception as e:
        print(f"❌ Error setting up country multipliers: {e}")
        sys.exit(1)
