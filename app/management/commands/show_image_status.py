from django.core.management.base import BaseCommand
from app.models import (
    GoldCategory, SilverCategory, ImitationCategory,
    GoldSubCategory, SilverSubCategory, ImitationSubCategory
)

class Command(BaseCommand):
    help = 'Show the current image status for all categories and subcategories'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== IMAGE STATUS REPORT ===\n'))

        # Gold Categories
        self.stdout.write(self.style.WARNING('GOLD CATEGORIES:'))
        gold_cats = GoldCategory.objects.all()
        gold_with_images = gold_cats.filter(image__isnull=False).exclude(image='').count()
        self.stdout.write(f'  • Total: {gold_cats.count()}')
        self.stdout.write(f'  • With Images: {gold_with_images}')
        self.stdout.write(f'  • Without Images: {gold_cats.count() - gold_with_images}\n')

        # Gold SubCategories
        self.stdout.write(self.style.WARNING('GOLD SUBCATEGORIES:'))
        gold_subcats = GoldSubCategory.objects.all()
        gold_sub_with_images = gold_subcats.filter(image__isnull=False).exclude(image='').count()
        self.stdout.write(f'  • Total: {gold_subcats.count()}')
        self.stdout.write(f'  • With Images: {gold_sub_with_images}')
        self.stdout.write(f'  • Without Images: {gold_subcats.count() - gold_sub_with_images}\n')

        # Silver Categories
        self.stdout.write(self.style.WARNING('SILVER CATEGORIES:'))
        silver_cats = SilverCategory.objects.all()
        silver_with_images = silver_cats.filter(image__isnull=False).exclude(image='').count()
        self.stdout.write(f'  • Total: {silver_cats.count()}')
        self.stdout.write(f'  • With Images: {silver_with_images}')
        self.stdout.write(f'  • Without Images: {silver_cats.count() - silver_with_images}\n')

        # Silver SubCategories
        self.stdout.write(self.style.WARNING('SILVER SUBCATEGORIES:'))
        silver_subcats = SilverSubCategory.objects.all()
        silver_sub_with_images = silver_subcats.filter(image__isnull=False).exclude(image='').count()
        self.stdout.write(f'  • Total: {silver_subcats.count()}')
        self.stdout.write(f'  • With Images: {silver_sub_with_images}')
        self.stdout.write(f'  • Without Images: {silver_subcats.count() - silver_sub_with_images}\n')

        # Imitation Categories
        self.stdout.write(self.style.WARNING('IMITATION CATEGORIES:'))
        imitation_cats = ImitationCategory.objects.all()
        imitation_with_images = imitation_cats.filter(image__isnull=False).exclude(image='').count()
        self.stdout.write(f'  • Total: {imitation_cats.count()}')
        self.stdout.write(f'  • With Images: {imitation_with_images}')
        self.stdout.write(f'  • Without Images: {imitation_cats.count() - imitation_with_images}\n')

        # Imitation SubCategories
        self.stdout.write(self.style.WARNING('IMITATION SUBCATEGORIES:'))
        imitation_subcats = ImitationSubCategory.objects.all()
        imitation_sub_with_images = imitation_subcats.filter(image__isnull=False).exclude(image='').count()
        self.stdout.write(f'  • Total: {imitation_subcats.count()}')
        self.stdout.write(f'  • With Images: {imitation_sub_with_images}')
        self.stdout.write(f'  • Without Images: {imitation_subcats.count() - imitation_sub_with_images}\n')

        # Summary
        total_categories = gold_cats.count() + silver_cats.count() + imitation_cats.count()
        total_subcategories = gold_subcats.count() + silver_subcats.count() + imitation_subcats.count()
        total_with_images = (gold_with_images + silver_with_images + imitation_with_images + 
                           gold_sub_with_images + silver_sub_with_images + imitation_sub_with_images)
        total_items = total_categories + total_subcategories

        self.stdout.write(self.style.SUCCESS('=== SUMMARY ==='))
        self.stdout.write(f'📊 Total Categories: {total_categories}')
        self.stdout.write(f'📊 Total SubCategories: {total_subcategories}')
        self.stdout.write(f'📊 Total Items: {total_items}')
        self.stdout.write(f'🖼️  Items with Images: {total_with_images}')
        self.stdout.write(f'📈 Coverage: {(total_with_images/total_items*100):.1f}%')
        
        if total_with_images == total_items:
            self.stdout.write(self.style.SUCCESS('\n🎉 ALL CATEGORIES AND SUBCATEGORIES HAVE IMAGES!'))
        else:
            self.stdout.write(self.style.WARNING(f'\n⚠️  {total_items - total_with_images} items still need images.'))
