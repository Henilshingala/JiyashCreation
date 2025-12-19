from django import template
from django.db.models import Q
from ..models import GoldCategory, SilverCategory, ImitationCategory, GoldProduct, SilverProduct, ImitationProduct

register = template.Library()

@register.filter
def active_categories_only(queryset):
    """Filter queryset to only include active categories"""
    return queryset.filter(is_active=True)

@register.filter
def active_subcategories_only(queryset):
    """Filter queryset to only include active subcategories"""
    return queryset.filter(is_active=True)

@register.filter
def active_products_only(queryset):
    """Filter products to only include those with active categories and subcategories"""
    return queryset.filter(
        is_active=True,
        category__is_active=True,
        subcategory__is_active=True
    )

@register.inclusion_tag('app/partials/category_menu.html')
def render_category_menu(category_type):
    """Render category menu with only active categories and subcategories"""
    categories = []
    
    if category_type.lower() == 'gold':
        categories = GoldCategory.objects.filter(is_active=True).prefetch_related(
            'subcategory'
        )
        for category in categories:
            category.active_subcategories = category.subcategory.filter(is_active=True)
    elif category_type.lower() == 'silver':
        categories = SilverCategory.objects.filter(is_active=True).prefetch_related(
            'subcategory'
        )
        for category in categories:
            category.active_subcategories = category.subcategory.filter(is_active=True)
    elif category_type.lower() == 'imitation':
        categories = ImitationCategory.objects.filter(is_active=True).prefetch_related(
            'subcategory'
        )
        for category in categories:
            category.active_subcategories = category.subcategory.filter(is_active=True)
    
    return {
        'categories': categories,
        'category_type': category_type.lower()
    }

@register.simple_tag
def get_active_product_count(category_type, category_id=None, subcategory_id=None):
    """Get count of active products for a category or subcategory"""
    model_map = {
        'gold': GoldProduct,
        'silver': SilverProduct,
        'imitation': ImitationProduct,
    }
    
    model = model_map.get(category_type.lower())
    if not model:
        return 0
    
    queryset = model.objects.all()  # Uses custom manager with active filtering
    
    if subcategory_id:
        queryset = queryset.filter(subcategory_id=subcategory_id)
    elif category_id:
        queryset = queryset.filter(category_id=category_id)
    
    return queryset.count()

@register.simple_tag
def is_category_available(category):
    """Check if a category has any available products"""
    if not category.is_active:
        return False
    
    # Check if category has any active products
    if hasattr(category, 'gold_products'):
        return category.gold_products.filter(
            is_active=True,
            subcategory__is_active=True
        ).exists()
    elif hasattr(category, 'silver_products'):
        return category.silver_products.filter(
            is_active=True,
            subcategory__is_active=True
        ).exists()
    elif hasattr(category, 'imitation_products'):
        return category.imitation_products.filter(
            is_active=True,
            subcategory__is_active=True
        ).exists()
    
    return False
