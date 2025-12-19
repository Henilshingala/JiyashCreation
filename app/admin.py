from django.contrib import admin
from django import forms
from .models import (
    Category, GoldCategory, GoldSubCategory,
    SilverCategory, SilverSubCategory, ImitationCategory, ImitationSubCategory,
    GoldProduct, SilverProduct, ImitationProduct,
    User, CountryMultiplier, Wishlist, Cart, Order, Payment, Review, CarouselSlider, EnhancedWishlist
)

class ColorWidget(forms.TextInput):
    input_type = 'color'
    def __init__(self, attrs=None):
        default_attrs = {'style': 'width: 60px; height: 35px; border: 2px solid #ddd; border-radius: 6px; cursor: pointer;'}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

class CarouselSliderForm(forms.ModelForm):
    class Meta:
        model = CarouselSlider
        fields = '__all__'
        widgets = {
            'title_color': ColorWidget(),
            'subtitle_color': ColorWidget(),
            'button_color': ColorWidget(),
        }

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'get_related_counts')
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    search_fields = ('name',)
    actions = ['activate_all_related_items', 'deactivate_all_related_items']
    
    def get_related_counts(self, obj):
        """Display counts of related subcategories and products"""
        category_name = obj.name.lower()
        
        if category_name == 'gold':
            subcategories = GoldSubCategory.objects.count()
            products = GoldProduct.objects.count()
        elif category_name == 'silver':
            subcategories = SilverSubCategory.objects.count()
            products = SilverProduct.objects.count()
        elif category_name == 'imitation':
            subcategories = ImitationSubCategory.objects.count()
            products = ImitationProduct.objects.count()
        else:
            subcategories = products = 0
            
        return f"{subcategories} subcategories, {products} products"
    get_related_counts.short_description = "Related Items"
    
    def activate_all_related_items(self, request, queryset):
        """Admin action to activate all related items for selected categories"""
        updated = 0
        for category in queryset:
            category.activate_all_related()
            updated += 1
        
        self.message_user(
            request,
            f"Successfully activated {updated} categories and all their related items."
        )
    activate_all_related_items.short_description = "Activate selected categories and all related items"
    
    def deactivate_all_related_items(self, request, queryset):
        """Admin action to deactivate all related items for selected categories"""
        updated = 0
        for category in queryset:
            category.deactivate_all_related()
            updated += 1
        
        self.message_user(
            request,
            f"Successfully deactivated {updated} categories and all their related items."
        )
    deactivate_all_related_items.short_description = "Deactivate selected categories and all related items"
    
    def save_model(self, request, obj, form, change):
        """Override save to show cascade message"""
        if change and 'is_active' in form.changed_data:
            old_obj = Category.objects.get(pk=obj.pk)
            if old_obj.is_active != obj.is_active:
                action = "activated" if obj.is_active else "deactivated"
                self.message_user(
                    request,
                    f"Category '{obj.name}' has been {action}. All related subcategories and products have been {action} as well.",
                    level='INFO'
                )
        super().save_model(request, obj, form, change)

@admin.register(GoldCategory)
class GoldCategorysAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)

@admin.register(GoldSubCategory)
class GoldSubCategorysAdmin(admin.ModelAdmin):
    list_display = ('gold_category', 'name', 'is_active')
    list_filter = ('gold_category', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)

@admin.register(SilverCategory)
class SilverCategorysAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)

@admin.register(SilverSubCategory)
class SilverSubCategorysAdmin(admin.ModelAdmin):
    list_display = ('silver_category', 'name', 'is_active')
    list_filter = ('silver_category', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)

@admin.register(ImitationCategory)
class ImitationCategorysAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)

@admin.register(ImitationSubCategory)
class ImitationSubCategorysAdmin(admin.ModelAdmin):
    list_display = ('imitation_category', 'name', 'is_active')
    list_filter = ('imitation_category', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)

@admin.register(GoldProduct)
class GoldProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'subcategory', 'original_price', 'selling_price', 'is_active', 'created_at')
    list_filter = ('category', 'subcategory', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)

@admin.register(SilverProduct)
class SilverProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'subcategory', 'original_price', 'selling_price', 'is_active', 'created_at')
    list_filter = ('category', 'subcategory', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)

@admin.register(ImitationProduct)
class ImitationProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'subcategory', 'original_price', 'selling_price', 'is_active', 'created_at')
    list_filter = ('category', 'subcategory', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('name',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone_number', 'gender', 'city', 'state')
    search_fields = ('first_name', 'last_name', 'email', 'phone_number')

@admin.register(CountryMultiplier)
class CountryMultiplierAdmin(admin.ModelAdmin):
    list_display = ('country_name', 'multiplier')
    def has_add_permission(self, request):
        return CountryMultiplier.objects.count() < 2
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_product', 'added_at')
    list_filter = ('user', 'content_type')
    def get_product(self, obj):
        return str(obj.product)
    get_product.short_description = 'Product'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_product', 'quantity', 'added_at')
    list_filter = ('user', 'content_type')
    def get_product(self, obj):
        return str(obj.product)
    get_product.short_description = 'Product'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_product', 'quantity', 'status', 'ordered_at')
    list_filter = ('status', 'ordered_at', 'content_type')
    search_fields = ('user__first_name', 'user__last_name')
    def get_product(self, obj):
        return str(obj.product)
    get_product.short_description = 'Product'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'payment_method', 'amount', 'payment_status', 'paid_at')
    list_filter = ('payment_method', 'payment_status')

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('get_product', 'user', 'star_rating', 'heading')
    list_filter = ('star_rating', 'content_type')
    search_fields = ('heading', 'description')
    def get_product(self, obj):
        return str(obj.product)
    get_product.short_description = 'Product'

@admin.register(EnhancedWishlist)
class EnhancedWishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_product', 'created_at')
    list_filter = ('created_at', 'content_type')
    search_fields = ('user__first_name', 'user__last_name')
    readonly_fields = ('created_at',)
    def get_product(self, obj):
        return str(obj.product)
    get_product.short_description = 'Product'
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(CarouselSlider)
class CarouselSliderAdmin(admin.ModelAdmin):
    form = CarouselSliderForm
    list_display = ('title', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'subtitle')
    ordering = ['order', '-created_at']
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Content', {
            'fields': ('image', 'title', 'subtitle', 'button_name', 'button_link')
        }),
        ('Colors', {
            'fields': ('title_color', 'subtitle_color', 'button_color'),
            'description': 'Customize the colors for different elements'
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    class Media:
        css = {
            'all': ('admin/css/color_picker.css',)
        }
        js = ('admin/js/color_picker.js',)
