from django import template
from django.urls import reverse

register = template.Library()

@register.simple_tag
def product_detail_url(product_type, product_id):
    """Generate the correct product detail URL based on product type."""
    url_names = {
        'gold': 'app:product_detail_gold',
        'silver': 'app:product_detail_silver',
        'imitation': 'app:product_detail_imitation',
    }
    
    url_name = url_names.get(product_type)
    if url_name:
        return reverse(url_name, kwargs={'pk': product_id})
    else:
        # Fallback to old URL pattern
        return reverse('app:product_detail', kwargs={'product_type': product_type, 'pk': product_id})

@register.simple_tag
def add_to_cart_url(product_type, product_id):
    """Generate the correct add to cart URL based on product type."""
    url_names = {
        'gold': 'app:add_to_cart_gold',
        'silver': 'app:add_to_cart_silver',
        'imitation': 'app:add_to_cart_imitation',
    }
    
    url_name = url_names.get(product_type)
    if url_name:
        return reverse(url_name, kwargs={'product_id': product_id})
    else:
        # Fallback to old URL pattern
        return reverse('app:add_to_cart', kwargs={'product_id': product_id})
