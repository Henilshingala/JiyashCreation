from .models import Category, GoldCategory, SilverCategory, ImitationCategory


def header_categories(request):
    """
    Provide up to 3 active top-level categories (Category model) for the header.
    Returns a list of dicts: {type (lowercased name for URL), name}
    """
    try:
        qs = Category.objects.filter(is_active=True).order_by('name')[:3]
        items = [
            {
                'type': (c.name or '').lower(),
                'name': c.name,
            }
            for c in qs
        ]
    except Exception:
        items = []
    return {'header_categories': items}

def active_categories(request):
    """
    Provide all active categories and subcategories for navigation menus
    """
    try:
        categories = {
            'gold_categories': GoldCategory.objects.filter(is_active=True).order_by('name'),
            'silver_categories': SilverCategory.objects.filter(is_active=True).order_by('name'),
            'imitation_categories': ImitationCategory.objects.filter(is_active=True).order_by('name'),
        }
        
        # Get active subcategories for each category type
        categories['gold_subcategories'] = {}
        categories['silver_subcategories'] = {}
        categories['imitation_subcategories'] = {}
        
        for gold_cat in categories['gold_categories']:
            categories['gold_subcategories'][gold_cat.id] = gold_cat.subcategory.filter(is_active=True)
            
        for silver_cat in categories['silver_categories']:
            categories['silver_subcategories'][silver_cat.id] = silver_cat.subcategory.filter(is_active=True)
            
        for imitation_cat in categories['imitation_categories']:
            categories['imitation_subcategories'][imitation_cat.id] = imitation_cat.subcategory.filter(is_active=True)
            
    except Exception:
        categories = {
            'gold_categories': [],
            'silver_categories': [],
            'imitation_categories': [],
            'gold_subcategories': {},
            'silver_subcategories': {},
            'imitation_subcategories': {},
        }
    
    return categories
