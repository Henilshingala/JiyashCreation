from django.core.management.base import BaseCommand
from django.db import transaction
from app.models import (
    Category, GoldCategory, SilverCategory, ImitationCategory,
    GoldSubCategory, SilverSubCategory, ImitationSubCategory,
    GoldProduct, SilverProduct, ImitationProduct
)

class Command(BaseCommand):
    help = 'Update category and subcategory active status and show impact on products'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category-type',
            type=str,
            choices=['gold', 'silver', 'imitation'],
            help='Type of category to update'
        )
        parser.add_argument(
            '--category-id',
            type=int,
            help='ID of the category to update'
        )
        parser.add_argument(
            '--subcategory-id',
            type=int,
            help='ID of the subcategory to update'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['active', 'inactive'],
            required=True,
            help='Set status to active or inactive'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes'
        )

    def handle(self, *args, **options):
        category_type = options.get('category_type')
        category_id = options.get('category_id')
        subcategory_id = options.get('subcategory_id')
        status = options['status'] == 'active'
        dry_run = options.get('dry_run', False)

        if not any([category_type, category_id, subcategory_id]):
            self.stdout.write(
                self.style.ERROR('Must specify at least one of: --category-type, --category-id, --subcategory-id')
            )
            return

        with transaction.atomic():
            if subcategory_id:
                self._update_subcategory(subcategory_id, status, dry_run)
            elif category_id:
                self._update_category(category_id, category_type, status, dry_run)
            elif category_type:
                self._update_category_type(category_type, status, dry_run)

    def _update_subcategory(self, subcategory_id, status, dry_run):
        # Try to find subcategory in all types
        subcategory = None
        category_type = None
        
        for model, cat_type in [
            (GoldSubCategory, 'gold'),
            (SilverSubCategory, 'silver'),
            (ImitationSubCategory, 'imitation')
        ]:
            try:
                subcategory = model.objects.get(id=subcategory_id)
                category_type = cat_type
                break
            except model.DoesNotExist:
                continue
        
        if not subcategory:
            self.stdout.write(
                self.style.ERROR(f'Subcategory with ID {subcategory_id} not found')
            )
            return

        # Get affected products
        product_model = {
            'gold': GoldProduct,
            'silver': SilverProduct,
            'imitation': ImitationProduct
        }[category_type]
        
        affected_products = product_model.all_objects.filter(subcategory=subcategory)
        
        self.stdout.write(f'Subcategory: {subcategory.name} ({category_type})')
        self.stdout.write(f'Current status: {"Active" if subcategory.is_active else "Inactive"}')
        self.stdout.write(f'New status: {"Active" if status else "Inactive"}')
        self.stdout.write(f'Affected products: {affected_products.count()}')
        
        if not dry_run:
            subcategory.is_active = status
            subcategory.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated subcategory {subcategory.name}')
            )

    def _update_category(self, category_id, category_type, status, dry_run):
        model_map = {
            'gold': GoldCategory,
            'silver': SilverCategory,
            'imitation': ImitationCategory
        }
        
        if not category_type:
            self.stdout.write(
                self.style.ERROR('Must specify --category-type when using --category-id')
            )
            return
            
        model = model_map.get(category_type)
        if not model:
            self.stdout.write(
                self.style.ERROR(f'Invalid category type: {category_type}')
            )
            return
        
        try:
            category = model.objects.get(id=category_id)
        except model.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Category with ID {category_id} not found')
            )
            return

        # Get affected products and subcategories
        product_model = {
            'gold': GoldProduct,
            'silver': SilverProduct,
            'imitation': ImitationProduct
        }[category_type]
        
        affected_products = product_model.all_objects.filter(category=category)
        affected_subcategories = category.subcategory.all()
        
        self.stdout.write(f'Category: {category.name} ({category_type})')
        self.stdout.write(f'Current status: {"Active" if category.is_active else "Inactive"}')
        self.stdout.write(f'New status: {"Active" if status else "Inactive"}')
        self.stdout.write(f'Affected subcategories: {affected_subcategories.count()}')
        self.stdout.write(f'Affected products: {affected_products.count()}')
        
        if not dry_run:
            category.is_active = status
            category.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated category {category.name}')
            )

    def _update_category_type(self, category_type, status, dry_run):
        model_map = {
            'gold': (GoldCategory, GoldProduct),
            'silver': (SilverCategory, SilverProduct),
            'imitation': (ImitationCategory, ImitationProduct)
        }
        
        category_model, product_model = model_map[category_type]
        
        categories = category_model.objects.all()
        affected_products = product_model.all_objects.all()
        
        self.stdout.write(f'Category type: {category_type}')
        self.stdout.write(f'New status: {"Active" if status else "Inactive"}')
        self.stdout.write(f'Affected categories: {categories.count()}')
        self.stdout.write(f'Affected products: {affected_products.count()}')
        
        if not dry_run:
            categories.update(is_active=status)
            self.stdout.write(
                self.style.SUCCESS(f'Updated all {category_type} categories')
            )
