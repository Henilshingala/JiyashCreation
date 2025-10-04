from django.shortcuts import redirect
from django.urls import resolve
from .models import GoldProduct, SilverProduct, ImitationProduct

class CategoryActiveMiddleware:
    """
    Middleware to automatically redirect users from inactive category product pages
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if this is a product detail page
        try:
            resolved = resolve(request.path)
            if resolved.url_name == 'product_detail':
                product_type = resolved.kwargs.get('product_type')
                pk = resolved.kwargs.get('pk')
                
                if product_type and pk:
                    model_map = {
                        'gold': GoldProduct,
                        'silver': SilverProduct,
                        'imitation': ImitationProduct,
                    }
                    
                    model = model_map.get(product_type.lower())
                    if model:
                        try:
                            product = model.all_objects.select_related('category', 'subcategory').get(pk=pk)
                            if not product.is_available():
                                return redirect('app:home')
                        except model.DoesNotExist:
                            pass  # Let the view handle 404
        except Exception:
            pass  # Continue with normal processing
        
        response = self.get_response(request)
        return response
