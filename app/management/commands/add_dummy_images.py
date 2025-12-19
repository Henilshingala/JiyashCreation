from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
import os
import random
from app.models import (
    GoldCategory, SilverCategory, ImitationCategory,
    GoldSubCategory, SilverSubCategory, ImitationSubCategory
)

class Command(BaseCommand):
    help = 'Add dummy images to all categories and subcategories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update images even if they already exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        dummy_images_dir = os.path.join(settings.BASE_DIR, 'media', 'dummy_images')
        
        if not os.path.exists(dummy_images_dir):
            self.stdout.write(
                self.style.ERROR(f'Dummy images directory not found: {dummy_images_dir}')
            )
            return

        # Image mappings for categories
        category_image_map = {
            # Gold categories
            'rings': 'gold_rings_category.jpg',
            'necklaces': 'gold_necklaces_category.jpg', 
            'earrings': 'gold_earrings_category.jpg',
            'bracelets': 'gold_bracelets_category.jpg',
            'chains': 'gold_chains_category.jpg',
        }

        # Image mappings for subcategories
        subcategory_image_map = {
            # Gold subcategories
            'wedding': 'gold_wedding_rings_subcategory.jpg',
            'engagement': 'gold_engagement_rings_subcategory.jpg',
            'casual': 'gold_casual_rings_subcategory.jpg',
            'statement': 'gold_statement_necklaces_subcategory.jpg',
            'pendant': 'gold_pendant_necklaces_subcategory.jpg',
            'choker': 'gold_choker_necklaces_subcategory.jpg',
        }

        # Process Gold Categories
        self.stdout.write('Processing Gold Categories...')
        gold_categories = GoldCategory.objects.all()
        for category in gold_categories:
            if not category.image or force:
                # Try to match category name to image
                image_file = self.find_matching_image(category.name, category_image_map, dummy_images_dir, 'gold', 'category')
                if image_file:
                    self.assign_image(category, image_file, 'Gold Category')

        # Process Silver Categories
        self.stdout.write('Processing Silver Categories...')
        silver_categories = SilverCategory.objects.all()
        for category in silver_categories:
            if not category.image or force:
                # Replace gold with silver in image filename
                image_file = self.find_matching_image(category.name, category_image_map, dummy_images_dir, 'silver', 'category')
                if image_file:
                    self.assign_image(category, image_file, 'Silver Category')

        # Process Imitation Categories
        self.stdout.write('Processing Imitation Categories...')
        imitation_categories = ImitationCategory.objects.all()
        for category in imitation_categories:
            if not category.image or force:
                # Replace gold with imitation in image filename
                image_file = self.find_matching_image(category.name, category_image_map, dummy_images_dir, 'imitation', 'category')
                if image_file:
                    self.assign_image(category, image_file, 'Imitation Category')

        # Process Gold SubCategories
        self.stdout.write('Processing Gold SubCategories...')
        gold_subcategories = GoldSubCategory.objects.all()
        for subcategory in gold_subcategories:
            if not subcategory.image or force:
                image_file = self.find_matching_image(subcategory.name, subcategory_image_map, dummy_images_dir, 'gold', 'subcategory')
                if image_file:
                    self.assign_image(subcategory, image_file, 'Gold SubCategory')

        # Process Silver SubCategories
        self.stdout.write('Processing Silver SubCategories...')
        silver_subcategories = SilverSubCategory.objects.all()
        for subcategory in silver_subcategories:
            if not subcategory.image or force:
                image_file = self.find_matching_image(subcategory.name, subcategory_image_map, dummy_images_dir, 'silver', 'subcategory')
                if image_file:
                    self.assign_image(subcategory, image_file, 'Silver SubCategory')

        # Process Imitation SubCategories
        self.stdout.write('Processing Imitation SubCategories...')
        imitation_subcategories = ImitationSubCategory.objects.all()
        for subcategory in imitation_subcategories:
            if not subcategory.image or force:
                image_file = self.find_matching_image(subcategory.name, subcategory_image_map, dummy_images_dir, 'imitation', 'subcategory')
                if image_file:
                    self.assign_image(subcategory, image_file, 'Imitation SubCategory')

        self.stdout.write(
            self.style.SUCCESS('Successfully added dummy images to all categories and subcategories!')
        )

    def find_matching_image(self, name, image_map, dummy_images_dir, material_type, category_type):
        """Find the best matching image for a category/subcategory name"""
        name_lower = name.lower()
        
        # Try exact matches first
        for key, filename in image_map.items():
            if key in name_lower:
                # Replace material type in filename
                if material_type == 'silver':
                    filename = filename.replace('gold_', 'silver_')
                elif material_type == 'imitation':
                    filename = filename.replace('gold_', 'imitation_')
                
                filepath = os.path.join(dummy_images_dir, filename)
                if os.path.exists(filepath):
                    return filepath
        
        # Fallback: get a random image of the correct type
        pattern = f"{material_type}_*_{category_type}.jpg"
        import glob
        matching_files = glob.glob(os.path.join(dummy_images_dir, pattern))
        if matching_files:
            return random.choice(matching_files)
        
        # Final fallback: any image of the correct type
        all_files = glob.glob(os.path.join(dummy_images_dir, f"*_{category_type}.jpg"))
        if all_files:
            return random.choice(all_files)
        
        return None

    def assign_image(self, instance, image_path, instance_type):
        """Assign an image to a category or subcategory instance"""
        try:
            with open(image_path, 'rb') as f:
                image_name = os.path.basename(image_path)
                instance.image.save(image_name, File(f), save=True)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Assigned {image_name} to {instance_type}: {instance.name}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to assign image to {instance_type}: {instance.name} - {str(e)}')
            )
