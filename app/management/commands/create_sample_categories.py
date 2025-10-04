from django.core.management.base import BaseCommand
from app.models import (
    GoldCategory, SilverCategory, ImitationCategory,
    GoldSubCategory, SilverSubCategory, ImitationSubCategory
)

class Command(BaseCommand):
    help = 'Create sample categories and subcategories for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample categories and subcategories...')

        # Define sample categories
        categories = [
            'Rings',
            'Necklaces', 
            'Earrings',
            'Bracelets',
            'Chains'
        ]

        # Define sample subcategories for each category
        subcategories_map = {
            'Rings': ['Wedding Rings', 'Engagement Rings', 'Casual Rings'],
            'Necklaces': ['Statement Necklaces', 'Pendant Necklaces', 'Choker Necklaces'],
            'Earrings': ['Stud Earrings', 'Drop Earrings', 'Hoop Earrings'],
            'Bracelets': ['Chain Bracelets', 'Bangle Bracelets', 'Charm Bracelets'],
            'Chains': ['Gold Chains', 'Silver Chains', 'Fashion Chains']
        }

        # Create Gold Categories and SubCategories
        self.stdout.write('Creating Gold categories...')
        for cat_name in categories:
            gold_cat, created = GoldCategory.objects.get_or_create(
                name=cat_name,
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'✓ Created Gold Category: {cat_name}')
            
            # Create subcategories
            for subcat_name in subcategories_map.get(cat_name, []):
                gold_subcat, created = GoldSubCategory.objects.get_or_create(
                    name=subcat_name,
                    gold_category=gold_cat,
                    defaults={'is_active': True}
                )
                if created:
                    self.stdout.write(f'  ✓ Created Gold SubCategory: {subcat_name}')

        # Create Silver Categories and SubCategories
        self.stdout.write('Creating Silver categories...')
        for cat_name in categories:
            silver_cat, created = SilverCategory.objects.get_or_create(
                name=cat_name,
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'✓ Created Silver Category: {cat_name}')
            
            # Create subcategories
            for subcat_name in subcategories_map.get(cat_name, []):
                silver_subcat, created = SilverSubCategory.objects.get_or_create(
                    name=subcat_name,
                    silver_category=silver_cat,
                    defaults={'is_active': True}
                )
                if created:
                    self.stdout.write(f'  ✓ Created Silver SubCategory: {subcat_name}')

        # Create Imitation Categories and SubCategories
        self.stdout.write('Creating Imitation categories...')
        for cat_name in categories:
            imitation_cat, created = ImitationCategory.objects.get_or_create(
                name=cat_name,
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'✓ Created Imitation Category: {cat_name}')
            
            # Create subcategories
            for subcat_name in subcategories_map.get(cat_name, []):
                imitation_subcat, created = ImitationSubCategory.objects.get_or_create(
                    name=subcat_name,
                    imitation_category=imitation_cat,
                    defaults={'is_active': True}
                )
                if created:
                    self.stdout.write(f'  ✓ Created Imitation SubCategory: {subcat_name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample categories and subcategories!')
        )
