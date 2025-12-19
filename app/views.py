from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Sum
from django.db import transaction, models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from decimal import Decimal
import json
import logging
import jwt
from functools import wraps
from django.conf import settings
from .models import (
    User, GoldProduct, SilverProduct, ImitationProduct,
    GoldCategory, SilverCategory, ImitationCategory,
    GoldSubCategory, SilverSubCategory, ImitationSubCategory,
    Wishlist, Cart, CarouselSlider, PasswordResetOTP,
    CountryMultiplier, Order, EnhancedWishlist,
)
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

logger = logging.getLogger(__name__)

JWT_SECRET = getattr(settings, "JWT_SECRET_KEY", None) or getattr(settings, "SECRET_KEY")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET_KEY or SECRET_KEY must be set")
JWT_ALGORITHM = "HS256"
JWT_EXP_DAYS = 7

def jwt_encode(payload):
    import datetime
    payload_copy = payload.copy()
    payload_copy["exp"] = datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXP_DAYS)
    return jwt.encode(payload_copy, JWT_SECRET, algorithm=JWT_ALGORITHM)

def jwt_decode(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None

def get_jwt_user(request):
    """Resolve user from JWT provided via Authorization header or cookies.
    Check Authorization header first, then fall back to cookies for browser navigation.
    """
    # First check Authorization header
    auth = request.headers.get("Authorization", "") or request.META.get("HTTP_AUTHORIZATION", "")
    token = None
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
    
    # If no Authorization header, check cookies
    if not token:
        token = request.COOKIES.get('jwt_token')
    
    if not token:
        return None
        
    data = jwt_decode(token)
    if not data:
        return None
    user_id = data.get("user_id")
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None

def get_country_multiplier(user):
    """Get the price multiplier based on user's country"""
    try:
        if user and hasattr(user, 'country') and user.country:
            user_country = user.country.lower().strip()
            
            # Check if user's country contains 'india' (handles 'India', 'india', 'India (IND)', etc.)
            if 'india' in user_country:
                multiplier_obj = CountryMultiplier.objects.filter(country_name='India').first()
                if multiplier_obj:
                    return multiplier_obj.multiplier
            else:
                # For all other countries
                multiplier_obj = CountryMultiplier.objects.filter(country_name='Others').first()
                if multiplier_obj:
                    return multiplier_obj.multiplier
        
        # Default fallback - for users without country set, use India multiplier
        india_multiplier = CountryMultiplier.objects.filter(country_name='India').first()
        if india_multiplier:
            return india_multiplier.multiplier
            
        # Final fallback
        return Decimal('1.0')
    except Exception as e:
        logger.error(f"Error getting country multiplier: {e}")
        return Decimal('1.0')

def apply_country_pricing(products, user):
    """Apply country-based pricing to products"""
    multiplier = get_country_multiplier(user)
    
    # Always apply pricing, even if multiplier is 1.0, to ensure consistency
    for product in products:
        # Handle original_price - check if it exists and is not None
        if hasattr(product, 'original_price') and product.original_price is not None:
            product.display_original_price = product.original_price * multiplier
        else:
            product.display_original_price = getattr(product, 'original_price', None)
            
        # Handle selling_price - check if it exists and is not None
        if hasattr(product, 'selling_price') and product.selling_price is not None:
            product.display_selling_price = product.selling_price * multiplier
        else:
            product.display_selling_price = getattr(product, 'selling_price', None)
        
        # Calculate display discount percentage based on adjusted prices
        try:
            if (product.display_original_price and product.display_selling_price and 
                product.display_original_price > product.display_selling_price):
                discount = ((product.display_original_price - product.display_selling_price) / 
                           product.display_original_price) * 100
                product.display_discount_percentage = int(discount)
            else:
                product.display_discount_percentage = 0
        except Exception:
            product.display_discount_percentage = 0
    
    return products

def jwt_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        user = get_jwt_user(request)
        if not user:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
            return redirect('app:login')
        request.custom_user = user
        return view_func(request, *args, **kwargs)
    return _wrapped

def _resolve_product_by_id(any_product_id):
    """Resolve a product by id from any of the product models.
    Returns (product_model, product_instance) or (None, None).
    """
    # Try gold/silver/imitation by id
    for model in (GoldProduct, SilverProduct, ImitationProduct):
        try:
            obj = model.objects.filter(id=any_product_id).first()
            if obj:
                return model, obj
        except Exception:
            continue
    return None, None

def get_product_url_name(product_type, url_type='detail'):
    """Get the correct URL name based on product type and URL type."""
    url_names = {
        'detail': {
            'gold': 'app:product_detail_gold',
            'silver': 'app:product_detail_silver', 
            'imitation': 'app:product_detail_imitation',
        },
        'add_to_cart': {
            'gold': 'app:add_to_cart_gold',
            'silver': 'app:add_to_cart_silver',
            'imitation': 'app:add_to_cart_imitation',
        }
    }
    return url_names.get(url_type, {}).get(product_type, f'app:product_{url_type}')

class ProductService:
    PRODUCT_TYPE_MAP = {
        'gold': GoldProduct,
        'silver': SilverProduct,
        'imitation': ImitationProduct,
    }

    @staticmethod
    def get_active_top_types():
        try:
            from .models import Category
            return set(c.name.lower() for c in Category.objects.filter(is_active=True))
        except Exception:
            return {'gold', 'silver', 'imitation'}

    @staticmethod
    def get_all_products(filters=None, sort_by=None, limit=None):
        if filters is None:
            filters = {}
        all_products = []
        active_types = ProductService.get_active_top_types()
        for p_type, model in ProductService.PRODUCT_TYPE_MAP.items():
            if p_type not in active_types:
                continue
            # Use the custom manager that automatically filters by active categories
            qs = model.objects.all()
            search_query = filters.get('q', '').strip()
            if search_query:
                qs = qs.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
            if 'min_price' in filters and filters['min_price']:
                try:
                    min_price = Decimal(str(filters['min_price']))
                    qs = qs.filter(selling_price__gte=min_price)
                except Exception:
                    pass
            if 'max_price' in filters and filters['max_price']:
                try:
                    max_price = Decimal(str(filters['max_price']))
                    qs = qs.filter(selling_price__lte=max_price)
                except Exception:
                    pass
            for product in qs:
                product.product_type = p_type
                all_products.append(product)
        if sort_by:
            sort_key_func, reverse = ProductService.get_sort_params(sort_by)
            all_products.sort(key=sort_key_func, reverse=reverse)
        if limit is not None:
            return all_products[:limit]
        return all_products

    @staticmethod
    def get_sort_params(sort_by):
        sort_options = {
            'newest': (lambda p: getattr(p, 'created_at', timezone.now()), True),
            'oldest': (lambda p: getattr(p, 'created_at', timezone.now()), False),
            'price_low': (lambda p: getattr(p, 'selling_price', 0), False),
            'price_high': (lambda p: getattr(p, 'selling_price', 0), True),
            'popular': (lambda p: getattr(p, 'created_at', timezone.now()), True),
            'name': (lambda p: p.name.lower(), False),
        }
        return sort_options.get(sort_by, sort_options['newest'])

class WishlistService:
    @staticmethod
    def get_wishlist_product_keys_for_user_profile(user_profile):
        if not user_profile:
            return set()
        return set(
            (w['content_type_id'], w['object_id'])
            for w in Wishlist.objects.filter(user=user_profile).values('content_type_id', 'object_id')
        )
    
    @staticmethod
    def get_wishlist_product_ids_for_user_profile(user_profile):
        """Get wishlist product IDs for a user profile (compatibility method)"""
        if not user_profile:
            return set()
        return WishlistService.get_wishlist_product_keys_for_user_profile(user_profile)

    @staticmethod
    def add_to_wishlist(user_profile, product_id):
        try:
            # Find the product in any of the product models
            model, product = _resolve_product_by_id(product_id)
            if not product:
                raise Http404("Product not found")
            
            # Use generic foreign key to reference the product
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(model)
            wishlist_item, created = Wishlist.objects.get_or_create(
                user=user_profile, 
                content_type=ct, 
                object_id=product.id
            )
            return wishlist_item, created, product
        except Exception as e:
            logger.error(f"Error adding to wishlist: {str(e)}")
            raise Http404("Product not found")

    @staticmethod
    def remove_from_wishlist(user_profile, product_id):
        try:
            # Find the product in any of the product models
            model, product = _resolve_product_by_id(product_id)
            if not product:
                raise Http404("Product not found")
            
            # Use generic foreign key to find and remove the wishlist item
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(model)
            removed_count, _ = Wishlist.objects.filter(
                user=user_profile, 
                content_type=ct, 
                object_id=product.id
            ).delete()
            return removed_count > 0, product
        except Exception as e:
            logger.error(f"Error removing from wishlist: {str(e)}")
            raise Http404("Product not found")

def get_product_model_and_instance(product_type, pk):
    model_map = {
        'gold': 'GoldProduct',
        'silver': 'SilverProduct',
        'imitation': 'ImitationProduct',
    }
    model_name = model_map.get(product_type.lower())
    if not model_name:
        return None, None
    model = apps.get_model('app', model_name)
    try:
        instance = model.objects.get(pk=pk)
        return model, instance
    except model.DoesNotExist:
        return model, None

@jwt_login_required
@require_POST
@csrf_exempt
def add_to_wishlist(request, product_type, pk):
    try:
        user_profile = getattr(request, 'custom_user', None)
        logger.info(f"Add to wishlist request: user={user_profile.id if user_profile else 'None'}, product_type={product_type}, pk={pk}")
        
        model, product = get_product_model_and_instance(product_type, pk)
        if not product:
            logger.error(f"Product not found: product_type={product_type}, pk={pk}")
            raise Http404("Product not found")
        
        logger.info(f"Found product: {product.name} (ID: {product.id}, Model: {model.__name__})")
        
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(model)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=user_profile, content_type=ct, object_id=product.id
        )
        
        logger.info(f"Wishlist operation: created={created}, item_id={wishlist_item.id if wishlist_item else 'None'}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'in_wishlist': True,
                'created': created,
                'product_id': product.id,
                'canonical_product_id': product.id,
                'product_type': product_type,
                'message': f'{product.name} {"added to" if created else "already in"} wishlist!',
                'action': 'add'
            })
        return redirect(request.META.get('HTTP_REFERER', 'app:wishlist'))
    except Http404:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        logger.error(f"Error adding to wishlist: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error adding to wishlist'}, status=500)

@jwt_login_required
@require_POST
@csrf_exempt
def remove_from_wishlist(request, product_type, pk):
    try:
        user_profile = getattr(request, 'custom_user', None)
        logger.info(f"Remove from wishlist request: user={user_profile.id if user_profile else 'None'}, product_type={product_type}, pk={pk}")
        
        model, product = get_product_model_and_instance(product_type, pk)
        if not product:
            logger.error(f"Product not found: product_type={product_type}, pk={pk}")
            raise Http404("Product not found")
        
        logger.info(f"Found product: {product.name} (ID: {product.id}, Model: {model.__name__})")
        
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(model)
        removed_count, _ = Wishlist.objects.filter(user=user_profile, content_type=ct, object_id=product.id).delete()
        removed = removed_count > 0
        
        logger.info(f"Wishlist removal: removed={removed}, count={removed_count}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'in_wishlist': False,
                'product_id': product.id,
                'product_type': product_type,
                'removed': removed,
                'message': f'{product.name} {"removed from" if removed else "not in"} wishlist!',
                'action': 'remove'
            })
        return redirect(request.META.get('HTTP_REFERER', 'app:wishlist'))
    except Exception as e:
        logger.error(f"Error removing from wishlist: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error removing from wishlist'}, status=500)

class CartService:
    @staticmethod
    def get_cart_count(user_profile):
        if not user_profile:
            return 0
        return Cart.objects.filter(user=user_profile).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0

    @staticmethod
    def get_cart_total(user_profile):
        if not user_profile:
            return 0
        total = 0
        for item in Cart.objects.filter(user=user_profile):
            product = item.product  # This uses the GenericForeignKey
            if product:
                price = getattr(product, 'selling_price', 0) or getattr(product, 'price', 0) or 0
                total += price * item.quantity
        return total

    @staticmethod
    def add_to_cart(user_profile, product_id, quantity=1, product_type=None):
        try:
            # If product_type is specified, use it directly for better performance
            if product_type and product_type in ProductService.PRODUCT_TYPE_MAP:
                model = ProductService.PRODUCT_TYPE_MAP[product_type]
                try:
                    product = model.objects.get(id=product_id)
                except model.DoesNotExist:
                    return None, False, None
            else:
                # Fallback: Find the product in any of the product models
                model, product = _resolve_product_by_id(product_id)
            if not product:
                raise Http404("Product not found")
            
            # Use generic foreign key to reference the product
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(model)
            cart_item, created = Cart.objects.get_or_create(
                user=user_profile, 
                content_type=ct,
                object_id=product.id,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return cart_item, created, product
        except Exception as e:
            logger.error(f"Error adding to cart: {str(e)}")
            raise

    @staticmethod
    def update_cart_item(user_profile, item_id, quantity):
        try:
            cart_item = Cart.objects.get(id=item_id, user=user_profile)
            if quantity <= 0:
                cart_item.delete()
                return None
            else:
                cart_item.quantity = quantity
                cart_item.save()
                return cart_item
        except Cart.DoesNotExist:
            raise Http404("Cart item not found")

    @staticmethod
    def remove_from_cart(user_profile, item_id):
        try:
            cart_item = Cart.objects.get(id=item_id, user=user_profile)
            cart_item.delete()
            return True
        except Cart.DoesNotExist:
            return False

def index(request):
    from django.db.models import Count
    carousel_sliders = CarouselSlider.objects.filter(is_active=True).order_by('order')
    
    # Build new arrivals list - only 3 most recent active products
    new_arrivals = []
    active_types = ProductService.get_active_top_types()
    for p_type, model in ProductService.PRODUCT_TYPE_MAP.items():
        if p_type not in active_types:
            continue
        # Get products from active categories only with optimized query
        products = model.objects.select_related('category', 'subcategory').filter(
            is_active=True,
            category__is_active=True,
            subcategory__is_active=True,
        ).order_by('-created_at')
        
        for product in products:
            product.product_type = p_type
            new_arrivals.append(product)
    
    # Sort all new arrivals by creation date and take only 3 most recent
    new_arrivals.sort(key=lambda p: getattr(p, 'created_at', timezone.now()), reverse=True)
    new_arrivals = new_arrivals[:3]
    
    # Calculate discount percentages for new arrivals
    for product in new_arrivals:
        try:
            op = getattr(product, 'original_price', None)
            sp = getattr(product, 'selling_price', None)
            if op and sp and op > sp:
                discount = (op - sp) / op * 100
                product.discount_percent = int(discount)
            else:
                product.discount_percent = 0
        except Exception:
            product.discount_percent = 0
    
    wishlist_keys = set()
    user = get_jwt_user(request)
    if user:
        wishlist_keys = WishlistService.get_wishlist_product_keys_for_user_profile(user)

    # Compute top 3 most wishlisted products from active categories only
    most_wishlisted = []
    has_wishlisted_products = False
    
    try:
        # Get all active products first
        all_active_products = []
        for p_type, model in ProductService.PRODUCT_TYPE_MAP.items():
            if p_type not in active_types:
                continue
            products = model.objects.select_related('category', 'subcategory').filter(
                is_active=True,
                category__is_active=True,
                subcategory__is_active=True,
            )
            for product in products:
                product.product_type = p_type
                all_active_products.append(product)
        
        # Aggregate wishlist counts by product id for active products only
        # Get ContentType objects once to avoid repeated queries
        content_types = {}
        for p_type, model in ProductService.PRODUCT_TYPE_MAP.items():
            if p_type in active_types:
                content_types[model] = ContentType.objects.get_for_model(model)
        
        # Build a map of (content_type_id, object_id) -> product for active products
        active_product_map = {}
        content_type_ids = set()
        
        for product in all_active_products:
            ct = content_types[type(product)]
            key = (ct.id, product.id)
            active_product_map[key] = product
            content_type_ids.add(ct.id)
        
        # Get wishlist counts for active products using GenericForeignKey
        counts = Wishlist.objects.filter(
            content_type_id__in=list(content_type_ids),
            object_id__in=[p.id for p in all_active_products]
        ).values('content_type_id', 'object_id').annotate(c=Count('id')).order_by('-c')
        
        counts_map = {(row['content_type_id'], row['object_id']): row['c'] for row in counts}
        
        # Build wishlisted products list
        for product in all_active_products:
            ct = content_types[type(product)]
            key = (ct.id, product.id)
            wishlist_count = counts_map.get(key, 0)
            if wishlist_count > 0:
                setattr(product, 'wishlist_count', wishlist_count)
                most_wishlisted.append(product)
                has_wishlisted_products = True
        
        # Sort by wishlist count (descending) and take top 3
        most_wishlisted.sort(key=lambda p: getattr(p, 'wishlist_count', 0), reverse=True)
        most_wishlisted = most_wishlisted[:3]
        
    except Exception as e:
        logger.error(f"Error computing top wishlisted: {str(e)}")
        most_wishlisted = []
        has_wishlisted_products = False
    
    # Apply country-based pricing to all products
    user = get_jwt_user(request)
    new_arrivals = apply_country_pricing(new_arrivals, user)
    most_wishlisted = apply_country_pricing(most_wishlisted, user)
    
    # When rendering products, set a tuple key for each product for wishlist check
    # Use the content_types we already have to avoid extra queries
    try:
        content_types_for_keys = {}
        for p_type, model in ProductService.PRODUCT_TYPE_MAP.items():
            if p_type in active_types:
                content_types_for_keys[model] = ContentType.objects.get_for_model(model)
        
        for product in new_arrivals:
            ct = content_types_for_keys.get(type(product))
            if ct:
                product.wishlist_key = (ct.id, product.id)
        for product in most_wishlisted:
            ct = content_types_for_keys.get(type(product))
            if ct:
                product.wishlist_key = (ct.id, product.id)
    except Exception as e:
        logger.error(f"Error setting wishlist keys: {str(e)}")
        # Fallback to individual queries if needed
        for product in new_arrivals:
            try:
                product.wishlist_key = (ContentType.objects.get_for_model(type(product)).id, product.id)
            except:
                pass
        for product in most_wishlisted:
            try:
                product.wishlist_key = (ContentType.objects.get_for_model(type(product)).id, product.id)
            except:
                pass
    
    context = {
        'carousel_sliders': carousel_sliders,
        'new_arrivals': new_arrivals,
        'most_wishlisted': most_wishlisted,
        'has_wishlisted_products': has_wishlisted_products,
        'wishlist_keys': wishlist_keys,
        'user_country': 'India',
        # Used by template to show "New Today" badge
        'today': timezone.now().date(),
    }
    return render(request, 'app/index.html', context)

def category_view(request, category_type, pk):
    category_models = {
        'gold': (GoldCategory, GoldSubCategory),
        'silver': (SilverCategory, SilverSubCategory),
        'imitation': (ImitationCategory, ImitationSubCategory),
    }
    if category_type not in category_models:
        raise Http404("Invalid category type")
    # Guard: hide if top-level category inactive
    if category_type not in ProductService.get_active_top_types():
        raise Http404("Invalid category type")
    category_model, subcategory_model = category_models[category_type]
    category = get_object_or_404(category_model, pk=pk, is_active=True)
    product_model = ProductService.PRODUCT_TYPE_MAP.get(category_type)
    products = product_model.objects.select_related('category', 'subcategory').filter(
        category=category,
        is_active=True,
        subcategory__is_active=True,
    ).order_by('-created_at')
    for product in products:
        product.product_type = category_type
    
    # Apply country-based pricing before pagination
    user = get_jwt_user(request)
    products = apply_country_pricing(products, user)
    
    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)
    wishlist_keys = set()
    if user:
        wishlist_keys = WishlistService.get_wishlist_product_keys_for_user_profile(user)
    
    # Convert wishlist keys to product IDs for template compatibility
    wishlist_ids = set()
    for product in products:
        from django.contrib.contenttypes.models import ContentType
        try:
            # Get the model class for this product
            if hasattr(product, 'product_type'):
                model_class = ProductService.PRODUCT_TYPE_MAP.get(product.product_type)
                if model_class:
                    ct = ContentType.objects.get_for_model(model_class)
                    key = (ct.id, product.id)
                    if key in wishlist_keys:
                        wishlist_ids.add(product.id)
        except Exception as e:
            logger.error(f"Error checking wishlist status for product {product.id}: {e}")
            continue
    
    context = {
        'category': category,
        'products': products,
        'category_type': category_type,
        'wishlist_ids': wishlist_ids,
        'user_country': 'India',
    }
    return render(request, 'app/category.html', context)

def subcategory_view(request, category_type, pk):
    category_models = {
        'gold': (GoldCategory, GoldSubCategory),
        'silver': (SilverCategory, SilverSubCategory),
        'imitation': (ImitationCategory, ImitationSubCategory),
    }
    if category_type not in category_models:
        raise Http404("Invalid category type")
    # Guard: hide if top-level category inactive
    if category_type not in ProductService.get_active_top_types():
        raise Http404("Invalid category type")
    category_model, subcategory_model = category_models[category_type]
    subcategory = get_object_or_404(subcategory_model, pk=pk, is_active=True)
    product_model = ProductService.PRODUCT_TYPE_MAP.get(category_type)
    products = product_model.objects.select_related('category', 'subcategory').filter(
        subcategory=subcategory,
        is_active=True,
        category__is_active=True,
    ).order_by('-created_at')
    for product in products:
        product.product_type = category_type
    
    # Apply country-based pricing before pagination
    user = get_jwt_user(request)
    products = apply_country_pricing(products, user)
    
    paginator = Paginator(products, 12)
    page = request.GET.get('page', 1)
    try:
        products = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        products = paginator.page(1)
    wishlist_keys = set()
    if user:
        wishlist_keys = WishlistService.get_wishlist_product_keys_for_user_profile(user)
    
    # Convert wishlist keys to product IDs for template compatibility
    wishlist_ids = set()
    for product in products:
        from django.contrib.contenttypes.models import ContentType
        try:
            # Get the model class for this product
            if hasattr(product, 'product_type'):
                model_class = ProductService.PRODUCT_TYPE_MAP.get(product.product_type)
                if model_class:
                    ct = ContentType.objects.get_for_model(model_class)
                    key = (ct.id, product.id)
                    if key in wishlist_keys:
                        wishlist_ids.add(product.id)
        except Exception as e:
            logger.error(f"Error checking wishlist status for product {product.id}: {e}")
            continue
    
    context = {
        'subcategory': subcategory,
        'products': products,
        'category_type': category_type,
        'wishlist_ids': wishlist_ids,
        'user_country': 'India',
    }
    return render(request, 'app/subcategory.html', context)

def product_detail(request, product_type, pk):
    product_model = ProductService.PRODUCT_TYPE_MAP.get(product_type)
    if not product_model or product_type not in ProductService.get_active_top_types():
        return redirect('app:home')
    try:
        # Use the custom manager that automatically filters by active categories
        product = product_model.objects.select_related('category', 'subcategory').get(pk=pk)
    except product_model.DoesNotExist:
        return redirect('app:home')
    product.product_type = product_type
    
    # Apply country-based pricing
    user = get_jwt_user(request)
    apply_country_pricing([product], user)
    
    # Map fields for template compatibility
    try:
        if not hasattr(product, 'title'):
            product.title = getattr(product, 'name', '')
        # Primary and additional images
        if hasattr(product, 'image1'):
            product.primary_image = product.image1
        if hasattr(product, 'image2'):
            product.image_2 = product.image2
        if hasattr(product, 'image3'):
            product.image_3 = product.image3
    except Exception:
        pass
    wishlist_ids = set()
    if user:
        wishlist_ids = WishlistService.get_wishlist_product_ids_for_user_profile(user)
    is_in_wishlist = (ContentType.objects.get_for_model(type(product)).id, product.id) in wishlist_ids
    related_products = list(product_model.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk).order_by('?')[:4])
    for related in related_products:
        related.product_type = product_type
    
    # Apply country pricing to related products
    apply_country_pricing(related_products, user)
    context = {
        'product': product,
        'product_type': product_type,
        'is_in_wishlist': is_in_wishlist,
        'related_products': related_products,
        'user_country': 'India',
    }
    return render(request, 'app/product_detail.html', context)

def shop_all(request):
    try:
        sort_by = request.GET.get('sort') or 'newest'
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        
        # Get all products to calculate price limits
        all_products = ProductService.get_all_products()
        
        if all_products:
            # Calculate price limits from all products
            prices = [p.selling_price for p in all_products if hasattr(p, 'selling_price') and p.selling_price]
            min_price_limit = min(prices) if prices else 0
            max_price_limit = max(prices) if prices else 10000  # Default max if no products
            
            # Get selected price values
            min_price_selected = float(min_price) if min_price and min_price.isdigit() else min_price_limit
            max_price_selected = float(max_price) if max_price and max_price.isdigit() else max_price_limit
            
            # Apply filters
            filters = {
                'q': request.GET.get('q', '').strip(),
                'min_price': min_price,
                'max_price': max_price,
            }
            filtered_products = ProductService.get_all_products(filters=filters, sort_by=sort_by)
        else:
            min_price_limit = 0
            max_price_limit = 10000
            min_price_selected = 0
            max_price_selected = 10000
            filtered_products = []
            filters = {}
        
        # Apply country-based pricing to filtered products
        user = get_jwt_user(request)
        filtered_products = apply_country_pricing(filtered_products, user)
        
        wishlist_keys = set()
        if user:
            wishlist_keys = WishlistService.get_wishlist_product_keys_for_user_profile(user)
        
        # Convert wishlist keys to product IDs for template compatibility
        wishlist_ids = set()
        for product in filtered_products:
            from django.contrib.contenttypes.models import ContentType
            try:
                # Get the model class for this product
                if hasattr(product, 'product_type'):
                    model_class = ProductService.PRODUCT_TYPE_MAP.get(product.product_type)
                    if model_class:
                        ct = ContentType.objects.get_for_model(model_class)
                        key = (ct.id, product.id)
                        if key in wishlist_keys:
                            wishlist_ids.add(product.id)
            except Exception as e:
                logger.error(f"Error checking wishlist status for product {product.id}: {e}")
                continue
            
        context = {
            'products': filtered_products,
            'total_products': len(filtered_products),
            'sort_by': sort_by,
            'filters': filters,
            'wishlist_ids': wishlist_ids,
            'min_price_limit': int(min_price_limit),
            'max_price_limit': int(max_price_limit),
            'min_price_selected': int(min_price_selected) if 'min_price_selected' in locals() else int(min_price_limit),
            'max_price_selected': int(max_price_selected) if 'max_price_selected' in locals() else int(max_price_limit),
        }
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Convert products to JSON-serializable format
            products_data = []
            for product in filtered_products:
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description or '',
                    'selling_price': float(getattr(product, 'display_selling_price', product.selling_price)) if getattr(product, 'display_selling_price', product.selling_price) else 0,
                    'original_price': float(getattr(product, 'display_original_price', getattr(product, 'original_price', None))) if getattr(product, 'display_original_price', getattr(product, 'original_price', None)) else None,
                    'product_type': product.product_type,
                    'image1_url': product.image1.url if product.image1 else None,
                }
                products_data.append(product_data)
            
            return JsonResponse({
                'products': products_data,
                'total_products': len(filtered_products),
                'sort_by': sort_by,
                'filters': filters,
            })
        
        return render(request, 'app/shop_all.html', context)
    except Exception as e:
        logger.error(f"Error in shop_all view: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Handle AJAX error response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'products': [],
                'total_products': 0,
                'error': 'An error occurred while loading products'
            }, status=500)
        
        return render(request, 'app/shop_all.html', {
            'products': [],
            'min_price_limit': 0,
            'max_price_limit': 10000,
            'min_price_selected': 0,
            'max_price_selected': 10000,
        })

def collection_view(request, collection_type):
    category_models = {
        'gold': GoldCategory,
        'silver': SilverCategory,
        'imitation': ImitationCategory,
    }
    if collection_type not in category_models:
        raise Http404('Invalid collection type')
    # Guard: hide if top-level category inactive
    if collection_type not in ProductService.get_active_top_types():
        raise Http404('Collection not available')
        
    category_model = category_models[collection_type]
    categories = category_model.objects.filter(is_active=True).order_by('name')
    
    # Use specific templates for each collection type
    template_map = {
        'gold': 'app/collection_gold.html',
        'silver': 'app/collection_silver.html',
        'imitation': 'app/collection_imitation.html',
    }
    
    template_name = template_map.get(collection_type, 'app/collection.html')
    
    context = {
        'collection_type': collection_type,
        'categories': categories,
    }
    return render(request, template_name, context)

@csrf_exempt
def signup(request):
    if request.method == 'POST':
        # Handle both JSON and form data
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
            else:
                # Handle form data
                data = {
                    'firstName': request.POST.get('firstName', ''),
                    'lastName': request.POST.get('lastName', ''),
                    'email': request.POST.get('email', ''),
                    'phone': request.POST.get('phone', ''),
                    'country': request.POST.get('country', ''),
                    'password': request.POST.get('password', ''),
                    'confirmPassword': request.POST.get('confirmPassword', ''),
                }
        except Exception as e:
            logger.error(f"Signup data parsing error: {str(e)}")
            return JsonResponse({'success': False, 'message': 'Invalid request format'}, status=400)
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirmPassword', '')
        
        # Validation
        if not email or not password:
            return JsonResponse({'success': False, 'message': 'Email and password are required'}, status=400)
        
        if password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Passwords do not match'}, status=400)
        
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'message': 'Email already registered'}, status=400)
        
        try:
            with transaction.atomic():
                user = User.objects.create(
                    first_name=data.get('firstName', ''),
                    last_name=data.get('lastName', ''),
                    email=email,
                    phone_number=data.get('phone', ''),
                    country=data.get('country', ''),
                    password=make_password(password),
                    confirm_password=make_password(confirm_password)
                )
                token = jwt_encode({'user_id': user.id, 'email': user.email})
                logger.info(f"User registered successfully: {email}")
                return JsonResponse({'success': True, 'message': 'Registration successful', 'token': token})
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return JsonResponse({'success': False, 'message': 'Registration failed'}, status=500)
    return render(request, 'app/signup.html')

def login_view(request):
    logger.info(f'Login request received. Method: {request.method}, Content-Type: {request.content_type}')
    
    if request.method == 'POST':
        try:
            # Handle both JSON and form data
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
                email = data.get('email', '').strip().lower()
                password = data.get('password', '')
            else:
                # Handle form data - try multiple field name variations
                email = (request.POST.get('loginEmail') or 
                        request.POST.get('email') or '').strip().lower()
                password = (request.POST.get('loginPassword') or 
                           request.POST.get('password') or '')
            
            logger.info(f'Login attempt for email: {email}')
            
            if not email or not password:
                logger.warning('Login failed: Email or password not provided')
                return JsonResponse({'success': False, 'message': 'Email and password are required'}, status=400)
                
            # Try to get user with the provided email
            try:
                user = User.objects.get(email=email)
                logger.info(f'User found: {user.email}')
                
                # Check the password using Django's built-in password verification
                if not check_password(password, user.password):
                    logger.warning(f'Invalid password for email: {email}')
                    return JsonResponse({'success': False, 'message': 'Invalid email or password'}, status=401)
            except User.DoesNotExist:
                logger.warning(f'User not found with email: {email}')
                return JsonResponse({'success': False, 'message': 'Invalid email or password'}, status=401)
            
            token = jwt_encode({'user_id': user.id, 'email': user.email})
            user_data = {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone if hasattr(user, 'phone') else ''
            }
            
            logger.info('Login successful')
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': user_data
            })
            
        except User.DoesNotExist:
            logger.warning(f'Login failed: Invalid credentials for email {email}')
            return JsonResponse({'success': False, 'message': 'Invalid email or password'}, status=401)
            
        except Exception as e:
            logger.error(f'Login error: {str(e)}', exc_info=True)
            return JsonResponse({'success': False, 'message': 'An error occurred during login'}, status=500)
    
    # Handle GET request
    return render(request, 'app/login.html')

def logout_view(request):
    return redirect('app:home')

@csrf_exempt
def forgot_password(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            email = data.get('email', '').strip().lower()
            
            if not email:
                return JsonResponse({'success': False, 'message': 'Email is required'}, status=400)
            
            # Check if user exists
            if not User.objects.filter(email=email).exists():
                # Don't reveal if email exists or not for security
                return JsonResponse({'success': True, 'message': 'If an account exists for this email, an OTP will be sent.'})
            
            # Generate and send OTP
            otp_instance = PasswordResetOTP.objects.create(email=email)
            
            # In a real application, you would send this via email
            # For now, we'll log it (in production, use proper email service)
            logger.info(f"Password reset OTP for {email}: {otp_instance.otp}")
            
            # Store OTP ID in session for verification
            request.session['reset_otp_id'] = otp_instance.id
            
            return JsonResponse({
                'success': True, 
                'message': 'OTP sent to your email address'
            })
            
        except Exception as e:
            logger.error(f"Error in forgot_password: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)
    
    return render(request, 'app/forgot_password.html')

@csrf_exempt
def verify_reset_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            otp = data.get('otp', '').strip()
            otp_id = data.get('otp_id') or request.session.get('reset_otp_id')
            
            if not otp or not otp_id:
                return JsonResponse({'success': False, 'message': 'OTP and OTP ID are required'}, status=400)
            
            try:
                otp_instance = PasswordResetOTP.objects.get(id=otp_id, otp=otp)
                
                if not otp_instance.is_valid():
                    return JsonResponse({'success': False, 'message': 'OTP has expired or been used'}, status=400)
                
                # Mark OTP as used
                otp_instance.is_used = True
                otp_instance.save()
                
                # Store verified OTP ID in session for password reset
                request.session['verified_otp_id'] = otp_id
                
                return JsonResponse({'success': True, 'message': 'OTP verified successfully'})
                
            except PasswordResetOTP.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Invalid OTP'}, status=400)
                
        except Exception as e:
            logger.error(f"Error in verify_reset_otp: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

@csrf_exempt
def reset_password_with_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            new_password = data.get('new_password', '')
            confirm_password = data.get('confirm_password', '')
            otp_id = data.get('otp_id') or request.session.get('verified_otp_id')
            
            if not new_password or not confirm_password:
                return JsonResponse({'success': False, 'message': 'Both password fields are required'}, status=400)
            
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'message': 'Passwords do not match'}, status=400)
            
            if len(new_password) < 8:
                return JsonResponse({'success': False, 'message': 'Password must be at least 8 characters long'}, status=400)
            
            if not otp_id:
                return JsonResponse({'success': False, 'message': 'Invalid session. Please restart the process'}, status=400)
            
            try:
                otp_instance = PasswordResetOTP.objects.get(id=otp_id, is_used=True)
                user = User.objects.get(email=otp_instance.email)
                
                # Update password
                user.password = make_password(new_password)
                user.save()
                
                # Clean up session
                request.session.pop('reset_otp_id', None)
                request.session.pop('verified_otp_id', None)
                
                return JsonResponse({'success': True, 'message': 'Password reset successfully'})
                
            except (PasswordResetOTP.DoesNotExist, User.DoesNotExist):
                return JsonResponse({'success': False, 'message': 'Invalid session'}, status=400)
                
        except Exception as e:
            logger.error(f"Error in reset_password_with_otp: {str(e)}")
            return JsonResponse({'success': False, 'message': 'An error occurred'}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)

def profile(request):
    # Render a shell; client-side JS will fetch data using JWT
    return render(request, 'app/profile.html')

@jwt_login_required
def profile_api(request):
    user_profile = getattr(request, 'custom_user', None)
    wishlist_count = Wishlist.objects.filter(user=user_profile).count() if user_profile else 0
    data = {
        'id': user_profile.id,
        'email': user_profile.email,
        'first_name': user_profile.first_name,
        'last_name': user_profile.last_name,
        'phone_number': getattr(user_profile, 'phone_number', ''),
        'birth_date': str(getattr(user_profile, 'birth_date', '') or ''),
        'address': {
            'house_number': getattr(user_profile, 'street_number', ''),
            'apartment_society': getattr(user_profile, 'apartment_society', ''),
            'street_name': getattr(user_profile, 'street_name', ''),
            'city': getattr(user_profile, 'city', ''),
            'state': getattr(user_profile, 'state', ''),
            'country': getattr(user_profile, 'country', ''),
            'pincode': getattr(user_profile, 'pincode', ''),
        },
        'wishlist_count': wishlist_count,
    }
    return JsonResponse({'success': True, 'user': data})

def profile_edit(request):
    # Render profile edit page
    return render(request, 'app/profile_edit.html')

def checkout(request):
    # Render checkout page (placeholder for now)
    return render(request, 'app/checkout.html')

@jwt_login_required
@csrf_exempt
def update_profile(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    try:
        user_profile = getattr(request, 'custom_user', None)
        data = json.loads(request.body.decode('utf-8'))
        
        # Update personal information
        user_profile.first_name = data.get('first_name', user_profile.first_name)
        user_profile.last_name = data.get('last_name', user_profile.last_name)
        user_profile.phone_number = data.get('phone_number', user_profile.phone_number)
        
        # Update birth date if provided
        birth_date = data.get('birth_date')
        if birth_date:
            user_profile.birth_date = birth_date
        
        # Check if country is being changed
        old_country = user_profile.country
        new_country = data.get('country', user_profile.country)
        country_changed = old_country != new_country
        
        
        # Update address information
        user_profile.street_number = data.get('street_number', user_profile.street_number)
        user_profile.street_name = data.get('street_name', user_profile.street_name)
        user_profile.country = new_country
        user_profile.state = data.get('state', user_profile.state)
        user_profile.city = data.get('city', user_profile.city)
        user_profile.pincode = data.get('pincode', user_profile.pincode)
        
        user_profile.save()
        
        message = 'Profile updated successfully'
        if country_changed:
            message += '. Please refresh the page to see updated prices for your country.'
        
        return JsonResponse({
            'success': True,
            'message': message,
            'country_changed': country_changed
        })
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Failed to update profile'
        }, status=500)

def wishlist_view(request):
    # Render shell; client-side will fetch wishlist via JWT API
    return render(request, 'app/wishlist.html')

@jwt_login_required
def wishlist_api(request):
    user_profile = getattr(request, 'custom_user', None)
    items = []
    try:
        # Optimize query with select_related for content_type
        qs = Wishlist.objects.filter(user=user_profile).select_related('content_type').order_by('-added_at')
        for w in qs[:100]:
            p = w.product
            if not p:
                continue
            # Get the primary image (different models use different field names)
            image_url = ''
            if hasattr(p, 'image1') and p.image1:
                image_url = p.image1.url
            elif hasattr(p, 'image') and p.image:
                image_url = p.image.url
            
            # Determine product type
            product_type = 'gold'  # default
            if isinstance(p, GoldProduct):
                product_type = 'gold'
            elif isinstance(p, SilverProduct):
                product_type = 'silver'
            elif isinstance(p, ImitationProduct):
                product_type = 'imitation'
            
            items.append({
                'id': p.id,
                'name': getattr(p, 'name', ''),
                'price': str(getattr(p, 'selling_price', 0) or 0),
                'image': image_url,
                'product_type': product_type,
            })
    except Exception as e:
        logger.error(f"wishlist_api error: {str(e)}")
    return JsonResponse({'success': True, 'items': items})

def about_us(request):
    return render(request, 'app/about.html')

def contact(request):
    return render(request, 'app/contact.html')

def faqs(request):
    return render(request, 'app/faqs.html')

def privacy_policies(request):
    return render(request, 'app/privacy_policies.html')

def terms_and_conditions(request):
    return render(request, 'app/terms_and_conditions.html')

@require_POST
@csrf_exempt
def check_email(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email', '').strip().lower()
        exists = User.objects.filter(email=email).exists()
        return JsonResponse({'exists': exists})
    except Exception:
        return JsonResponse({'exists': False}, status=400)

# Cart Views
def cart_view(request):
    user_profile = getattr(request, 'custom_user', None)
    
    # Check for JWT token in Authorization header first
    jwt_user = get_jwt_user(request)
    if jwt_user:
        user_profile = jwt_user
        request.custom_user = jwt_user
        logger.info(f"Cart access: JWT user found - {jwt_user.id}")
    
    # Security check - redirect to login if no authenticated user
    if not user_profile:
        logger.warning("Unauthenticated access attempt to cart page - no valid JWT token")
        next_url = request.build_absolute_uri()
        return redirect(f'/login/?next={next_url}')
    
    cart_items = []
    imitation_total = Decimal('0')
    silver_total = Decimal('0')
    gold_total = Decimal('0')
    
    DISCOUNT_SLABS = [ 
        (15000, 10),    
        (5000, 5),    
    ]
    
    try:
        items = Cart.objects.filter(user=user_profile).order_by('-added_at')
        logger.info(f"Cart items found for user {user_profile.id}: {items.count()}")
        
        # First pass: Loop through ALL cart items and calculate totals
        for item in items:
            product = item.product
            if not product:
                logger.warning(f"Cart item {item.id} has no product")
                continue
            
            # Determine product_type by checking which model the product belongs to
            product_type = None
            if isinstance(product, GoldProduct):
                product_type = 'gold'
            elif isinstance(product, SilverProduct):
                product_type = 'silver'
            elif isinstance(product, ImitationProduct):
                product_type = 'imitation'
            else:
                # Fallback: check by querying each model
                for p_type, model in ProductService.PRODUCT_TYPE_MAP.items():
                    try:
                        if model.objects.filter(id=product.id).exists():
                            product_type = p_type
                            break
                    except:
                        continue
                
                if not product_type:
                    product_type = 'gold'  # default fallback
            
            # Set product_type attribute for template usage
            product.product_type = product_type
            
            # Apply country-based pricing
            multiplier = get_country_multiplier(user_profile)
            base_price = Decimal(str(getattr(product, 'selling_price', 0) or 0))
            price = base_price * multiplier
            
            # Set display prices for template
            product.display_selling_price = price
            if hasattr(product, 'original_price') and product.original_price:
                product.display_original_price = Decimal(str(product.original_price)) * multiplier
            
            subtotal = price * item.quantity
            
            # Add to category-specific totals (ALWAYS, regardless of other products)
            if product_type == 'imitation':
                imitation_total += subtotal
            elif product_type == 'silver':
                silver_total += subtotal
            elif product_type == 'gold':
                gold_total += subtotal
            
            cart_items.append({
                'id': item.id,
                'product': product,
                'quantity': item.quantity,
                'price': price,
                'subtotal': subtotal,
            })
            logger.info(f"Added cart item: {product.name} x {item.quantity} (type: {product_type}, subtotal: {subtotal})")
    
    except Exception as e:
        logger.error(f"cart_view error: {str(e)}", exc_info=True)
    
    # Calculate raw total before discount
    total = imitation_total + silver_total + gold_total
    
    # Calculate discount for imitation products only (ALWAYS based on imitation_total alone)
    discount_percentage = 0
    discount_amount = Decimal('0')
    next_discount_amount = Decimal('0')
    next_discount_percentage = 0
    progress_percentage = 0
    base_progress = 0
    additional_progress = 0
    
    # Apply discount logic ONLY based on imitation_total, regardless of other products
    if imitation_total > 0:
        # Find applicable discount (check from highest to lowest)
        for threshold, percentage in DISCOUNT_SLABS:
            if imitation_total >= threshold:
                discount_percentage = percentage
                discount_amount = (imitation_total * Decimal(percentage)) / Decimal('100')
                break
        
        # Calculate progress percentage based on actual amount relative to milestones
        # Only 2 slabs: 5% at ₹5,000 and 10% at ₹15,000
        # Milestones are positioned at: 33% and 100% on the progress bar
        
        if imitation_total >= 15000:
            # At or beyond final milestone (10% discount)
            progress_percentage = 100
        elif imitation_total >= 5000:
            # Between 5% and 10% milestone (33% to 100% on bar)
            progress_in_range = float((imitation_total - 5000) / (15000 - 5000))
            progress_percentage = 33 + (progress_in_range * 67)
        else:
            # Between 0 and 5% milestone (0% to 33% on bar)
            progress_in_range = float(imitation_total / 5000)
            progress_percentage = progress_in_range * 33
        
        # Ensure progress doesn't exceed 100%
        progress_percentage = min(100, progress_percentage)
        
        # Find next milestone for messaging
        next_slab_found = False
        for threshold, percentage in DISCOUNT_SLABS:
            if imitation_total < threshold:
                next_discount_amount = Decimal(threshold) - imitation_total
                next_discount_percentage = percentage
                next_slab_found = True
                break
        
        # If maximum discount reached (10%)
        if not next_slab_found or discount_percentage == 10:
            progress_percentage = 100
            next_discount_amount = Decimal('0')
            next_discount_percentage = 0
    
    # Calculate final total: (imitation_total - discount) + silver_total + gold_total
    final_total = (imitation_total - discount_amount) + silver_total + gold_total
    
    logger.info(f"Cart totals - Imitation: {imitation_total}, Silver: {silver_total}, Gold: {gold_total}")
    logger.info(f"Discount: {discount_percentage}% = {discount_amount}, Final total: {final_total}")
    logger.info(f"Progress calculation - Imitation total: ₹{imitation_total}, Progress: {progress_percentage}%")
    
    context = {
        'cart_items': cart_items,
        'total': float(total),
        'final_total': float(final_total),
        'cart_count': len(cart_items),
        'imitation_total': float(imitation_total),
        'silver_total': float(silver_total),
        'gold_total': float(gold_total),
        'discount_percentage': discount_percentage,
        'discount_amount': float(discount_amount),
        'next_discount_amount': float(next_discount_amount),
        'next_discount_percentage': next_discount_percentage,
        'progress_percentage': progress_percentage,
    }
    
    return render(request, 'app/cart.html', context)

@jwt_login_required
def cart_api(request):
    user_profile = getattr(request, 'custom_user', None)
    items = []
    total = 0
    try:
        # Optimize query with select_related for content_type
        cart_items = Cart.objects.filter(user=user_profile).select_related('content_type').order_by('-added_at')
        for item in cart_items:
            product = item.product
            if not product:
                continue
            price = getattr(product, 'selling_price', 0) or 0
            subtotal = price * item.quantity
            total += subtotal
            
            # Get the primary image (different models use different field names)
            image_url = ''
            if hasattr(product, 'image1') and product.image1:
                image_url = product.image1.url
            elif hasattr(product, 'image') and product.image:
                image_url = product.image.url
            
            items.append({
                'id': item.id,
                'product_id': product.id,
                'name': getattr(product, 'name', ''),
                'price': str(price),
                'quantity': item.quantity,
                'subtotal': str(subtotal),
                'image': image_url,
            })
    except Exception as e:
        logger.error(f"cart_api error: {str(e)}")
    
    cart_count = CartService.get_cart_count(user_profile)
    return JsonResponse({
        'success': True, 
        'items': items, 
        'total': str(total),
        'count': cart_count,
        'cart_count': cart_count
    })

@require_POST
@csrf_exempt
def add_to_cart(request, product_id, product_type=None):
    try:
        # Check authentication first - require JWT token
        user_profile = get_jwt_user(request)
        if not user_profile:
            return JsonResponse({
                'success': False, 
                'message': 'Please login to add items to cart',
                'redirect': '/login/?next=' + request.build_absolute_uri()
            }, status=401)
        
        # Get quantity from request
        quantity = 1
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body.decode('utf-8'))
                quantity = int(data.get('quantity', 1))
            except:
                pass
        else:
            quantity = int(request.POST.get('quantity', 1))
        
        cart_item, created, product = CartService.add_to_cart(user_profile, product_id, quantity, product_type)
        cart_count = CartService.get_cart_count(user_profile)
        cart_total = CartService.get_cart_total(user_profile)
        
        logger.info(f"Add to cart - User: {user_profile.id}, Product: {product_id}, Created: {created}, Cart Count: {cart_count}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{product.name} {"added to" if created else "updated in"} cart!',
                'cart_count': cart_count,
                'cart_total': str(cart_total),
                'item_id': cart_item.id
            })
        return redirect(request.META.get('HTTP_REFERER', 'app:cart'))
    except Http404:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        logger.error(f"Error adding to cart: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error adding to cart'}, status=500)

@jwt_login_required
@require_POST
@csrf_exempt
def update_cart(request, item_id):
    try:
        user_profile = getattr(request, 'custom_user', None)
        
        # Get quantity from request
        if request.content_type == 'application/json':
            data = json.loads(request.body.decode('utf-8'))
            quantity = int(data.get('quantity', 1))
        else:
            quantity = int(request.POST.get('quantity', 1))
        
        cart_item = CartService.update_cart_item(user_profile, item_id, quantity)
        cart_count = CartService.get_cart_count(user_profile)
        cart_total = CartService.get_cart_total(user_profile)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if cart_item is None:
                return JsonResponse({
                    'success': True,
                    'message': 'Item removed from cart',
                    'cart_count': cart_count,
                    'cart_total': str(cart_total),
                    'removed': True
                })
            else:
                price = cart_item.product.selling_price or cart_item.product.price or 0
                subtotal = price * cart_item.quantity
                return JsonResponse({
                    'success': True,
                    'message': 'Cart updated successfully',
                    'cart_count': cart_count,
                    'cart_total': str(cart_total),
                    'item_subtotal': str(subtotal),
                    'quantity': cart_item.quantity
                })
        return redirect('app:cart')
    except Http404:
        return JsonResponse({'success': False, 'message': 'Cart item not found'}, status=404)
    except Exception as e:
        logger.error(f"Error updating cart: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error updating cart'}, status=500)

@jwt_login_required
@require_POST
@csrf_exempt
def remove_from_cart(request, item_id):
    try:
        user_profile = getattr(request, 'custom_user', None)
        removed = CartService.remove_from_cart(user_profile, item_id)
        cart_count = CartService.get_cart_count(user_profile)
        cart_total = CartService.get_cart_total(user_profile)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart' if removed else 'Item not found',
                'cart_count': cart_count,
                'cart_total': str(cart_total),
                'removed': removed
            })
        return redirect('app:cart')
    except Exception as e:
        logger.error(f"Error removing from cart: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error removing from cart'}, status=500)

# Duplicate functions removed - kept originals at end of file

# Duplicate wishlist functions removed

@csrf_exempt
def wishlist_status_api(request):
    """API endpoint to check wishlist status for multiple products"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed'}, status=405)
    
    # Check for authentication, but don't require it
    user_profile = get_jwt_user(request)
    if not user_profile:
        # Return empty wishlist status for non-authenticated users
        try:
            data = json.loads(request.body.decode('utf-8'))
            product_ids = data.get('product_ids', [])
            wishlist_status = {str(pid): False for pid in product_ids}
            return JsonResponse({
                'success': True,
                'wishlist_status': wishlist_status
            })
        except:
            return JsonResponse({'success': True, 'wishlist_status': {}})
    
    try:
        user_profile = getattr(request, 'custom_user', None)
        data = json.loads(request.body.decode('utf-8'))
        product_ids = data.get('product_ids', [])
        
        logger.info(f"Wishlist status check for user {user_profile.id if user_profile else 'None'}, products: {product_ids}")
        
        if not product_ids:
            return JsonResponse({'success': True, 'wishlist_status': {}})
        
        # Get all wishlist items for the user
        wishlist_items = Wishlist.objects.filter(user=user_profile).values('content_type_id', 'object_id')
        wishlist_keys = {(item['content_type_id'], item['object_id']) for item in wishlist_items}
        
        logger.info(f"User has {len(wishlist_keys)} wishlist items: {wishlist_keys}")
        
        # Check status for each product
        wishlist_status = {}
        for product_id in product_ids:
            # Find the product in any of the product models
            model, product = _resolve_product_by_id(product_id)
            if product:
                from django.contrib.contenttypes.models import ContentType
                ct = ContentType.objects.get_for_model(model)
                key = (ct.id, product.id)
                is_wishlisted = key in wishlist_keys
                wishlist_status[str(product_id)] = is_wishlisted
                logger.info(f"Product {product_id} ({model.__name__}): key={key}, wishlisted={is_wishlisted}")
            else:
                wishlist_status[str(product_id)] = False
                logger.warning(f"Product {product_id} not found")
        
        logger.info(f"Final wishlist status: {wishlist_status}")
        
        return JsonResponse({
            'success': True,
            'wishlist_status': wishlist_status
        })
    
    except Exception as e:
        logger.error(f"wishlist_status_api error: {str(e)}")
        return JsonResponse({'success': False, 'message': 'Error checking wishlist status'}, status=500)

