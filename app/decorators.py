from functools import wraps
from django.shortcuts import redirect
from django.http import Http404
from .models import GoldProduct, SilverProduct, ImitationProduct

def check_category_active(view_func):
    """
    Decorator to check if product's category and subcategory are active.
    Redirects to homepage if inactive.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Get product_type and pk from URL parameters
        product_type = kwargs.get('product_type')
        pk = kwargs.get('pk')
        
        if not product_type or not pk:
            return view_func(request, *args, **kwargs)
        
        # Map product types to models
        model_map = {
            'gold': GoldProduct,
            'silver': SilverProduct,
            'imitation': ImitationProduct,
        }
        
        model = model_map.get(product_type.lower())
        if not model:
            raise Http404("Invalid product type")
        
        try:
            # Use all_objects to bypass the custom manager filtering
            product = model.all_objects.select_related('category', 'subcategory').get(pk=pk)
            
            # Check if product and its categories are active
            if not product.is_available():
                return redirect('app:home')
                
        except model.DoesNotExist:
            raise Http404("Product not found")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

def require_active_categories(view_func):
    """
    Decorator to ensure only active categories are processed in views.
    Can be used on category listing views.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Add active category filtering context
        request.active_categories_only = True
        return view_func(request, *args, **kwargs)
    
    return wrapper
