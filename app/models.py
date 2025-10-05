from django.db import models
from django.utils import timezone
from decimal import Decimal
import random
import string
from .managers import ProductManager
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class Category(models.Model):
    CATEGORY_CHOICES = [
        ('Gold', 'Gold'),
        ('Silver', 'Silver'),
        ('Imitation', 'Imitation'),
    ]
    name = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True, default='Gold')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Category"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to handle cascading visibility changes"""
        # Check if is_active is being changed
        if self.pk:
            old_instance = Category.objects.get(pk=self.pk)
            if old_instance.is_active != self.is_active:
                self._cascade_visibility_change(self.is_active)
        else:
            # New instance - cascade the initial state
            self._cascade_visibility_change(self.is_active)
        
        super().save(*args, **kwargs)
    
    def _cascade_visibility_change(self, is_active):
        """Cascade visibility changes to all related subcategories and products"""
        category_name = self.name.lower()
        
        if category_name == 'gold':
            # Update all Gold categories and subcategories
            GoldCategory.objects.all().update(is_active=is_active)
            GoldSubCategory.objects.all().update(is_active=is_active)
            # Update all Gold products
            GoldProduct.objects.all().update(is_active=is_active)
            
        elif category_name == 'silver':
            # Update all Silver categories and subcategories
            SilverCategory.objects.all().update(is_active=is_active)
            SilverSubCategory.objects.all().update(is_active=is_active)
            # Update all Silver products
            SilverProduct.objects.all().update(is_active=is_active)
            
        elif category_name == 'imitation':
            # Update all Imitation categories and subcategories
            ImitationCategory.objects.all().update(is_active=is_active)
            ImitationSubCategory.objects.all().update(is_active=is_active)
            # Update all Imitation products
            ImitationProduct.objects.all().update(is_active=is_active)
    
    def activate_all_related(self):
        """Activate all related subcategories and products"""
        self.is_active = True
        self._cascade_visibility_change(True)
        self.save()
    
    def deactivate_all_related(self):
        """Deactivate all related subcategories and products"""
        self.is_active = False
        self._cascade_visibility_change(False)
        self.save()

class GoldCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, default='Unnamed Gold Category')
    image = models.ImageField(upload_to='gold_category/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Gold Category"
        verbose_name_plural = "Gold Category"
    def __str__(self):
        return self.name

class GoldSubCategory(models.Model):
    gold_category = models.ForeignKey(GoldCategory, on_delete=models.CASCADE, related_name='subcategory', default=1)
    name = models.CharField(max_length=100, default='Unnamed Gold SubCategory')
    image = models.ImageField(upload_to='gold_subcategory/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Gold SubCategory"
        verbose_name_plural = "Gold SubCategory"
    def __str__(self):
        return f"{self.gold_category.name} - {self.name}"

class SilverCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, default='Unnamed Silver Category')
    image = models.ImageField(upload_to='silver_category/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Silver Category"
        verbose_name_plural = "Silver Category"
    def __str__(self):
        return self.name

class SilverSubCategory(models.Model):
    silver_category = models.ForeignKey(SilverCategory, on_delete=models.CASCADE, related_name='subcategory', default=1)
    name = models.CharField(max_length=100, default='Unnamed Silver SubCategory')
    image = models.ImageField(upload_to='silver_subcategory/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Silver SubCategory"
        verbose_name_plural = "Silver SubCategory"
    def __str__(self):
        return f"{self.silver_category.name} - {self.name}"

class ImitationCategory(models.Model):
    name = models.CharField(max_length=100, unique=True, default='Unnamed Imitation Category')
    image = models.ImageField(upload_to='imitation_category/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Imitation Category"
        verbose_name_plural = "Imitation Category"
    def __str__(self):
        return self.name

class ImitationSubCategory(models.Model):
    imitation_category = models.ForeignKey(ImitationCategory, on_delete=models.CASCADE, related_name='subcategory', default=1)
    name = models.CharField(max_length=100, default='Unnamed Imitation SubCategory')
    image = models.ImageField(upload_to='imitation_subcategory/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    class Meta:
        verbose_name = "Imitation SubCategory"
        verbose_name_plural = "Imitation SubCategory"
    def __str__(self):
        return f"{self.imitation_category.name} - {self.name}"

class GoldProduct(models.Model):
    name = models.CharField(max_length=200, default='Unnamed Gold Product')
    description = models.TextField(blank=True, null=True, default='')
    image1 = models.ImageField(upload_to='gold_products/', blank=True, null=True)
    image2 = models.ImageField(upload_to='gold_products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='gold_products/', blank=True, null=True)
    video = models.FileField(upload_to='gold_products/videos/', blank=True, null=True)
    category = models.ForeignKey(GoldCategory, on_delete=models.CASCADE, related_name='gold_products', default=1)
    subcategory = models.ForeignKey(GoldSubCategory, on_delete=models.CASCADE, related_name='gold_products', default=1)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    carat_metal_purity = models.CharField(max_length=10, default='24k')
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ProductManager()
    all_objects = models.Manager()  # Access to all objects including inactive
    
    class Meta:
        verbose_name = "Gold Product"
        verbose_name_plural = "Gold Product"
    
    def __str__(self):
        return self.name
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.original_price and self.selling_price and self.original_price > self.selling_price:
            return ((self.original_price - self.selling_price) / self.original_price) * 100
        return 0
    
    def is_available(self):
        """Check if product and its categories are active"""
        return (self.is_active and 
                self.category.is_active and 
                self.subcategory.is_active)

class SilverProduct(models.Model):
    name = models.CharField(max_length=200, default='Unnamed Silver Product')
    description = models.TextField(blank=True, null=True, default='')
    image1 = models.ImageField(upload_to='silver_products/', blank=True, null=True)
    image2 = models.ImageField(upload_to='silver_products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='silver_products/', blank=True, null=True)
    video = models.FileField(upload_to='silver_products/videos/', blank=True, null=True)
    category = models.ForeignKey(SilverCategory, on_delete=models.CASCADE, related_name='silver_products', default=1)
    subcategory = models.ForeignKey(SilverSubCategory, on_delete=models.CASCADE, related_name='silver_products', default=1)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    purity = models.CharField(max_length=50, default='Sterling 92.5')
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ProductManager()
    all_objects = models.Manager()  # Access to all objects including inactive
    
    class Meta:
        verbose_name = "Silver Product"
        verbose_name_plural = "Silver Product"
    
    def __str__(self):
        return self.name
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.original_price and self.selling_price and self.original_price > self.selling_price:
            return ((self.original_price - self.selling_price) / self.original_price) * 100
        return 0
    
    def is_available(self):
        """Check if product and its categories are active"""
        return (self.is_active and 
                self.category.is_active and 
                self.subcategory.is_active)

class ImitationProduct(models.Model):
    name = models.CharField(max_length=200, default='Unnamed Imitation Product')
    description = models.TextField(blank=True, null=True, default='')
    image1 = models.ImageField(upload_to='imitation_products/', blank=True, null=True)
    image2 = models.ImageField(upload_to='imitation_products/', blank=True, null=True)
    image3 = models.ImageField(upload_to='imitation_products/', blank=True, null=True)
    video = models.FileField(upload_to='imitation_products/videos/', blank=True, null=True)
    category = models.ForeignKey(ImitationCategory, on_delete=models.CASCADE, related_name='imitation_products', default=1)
    subcategory = models.ForeignKey(ImitationSubCategory, on_delete=models.CASCADE, related_name='imitation_products', default=1)
    original_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    material_details = models.CharField(max_length=100, default='Brass')
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = ProductManager()
    all_objects = models.Manager()  # Access to all objects including inactive
    
    class Meta:
        verbose_name = "Imitation Product"
        verbose_name_plural = "Imitation Product"
    
    def __str__(self):
        return self.name
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.original_price and self.selling_price and self.original_price > self.selling_price:
            return ((self.original_price - self.selling_price) / self.original_price) * 100
        return 0
    
    def is_available(self):
        """Check if product and its categories are active"""
        return (self.is_active and 
                self.category.is_active and 
                self.subcategory.is_active)

class User(models.Model):
    first_name = models.CharField(max_length=100, default='John')
    last_name = models.CharField(max_length=100, default='Doe')
    email = models.EmailField(unique=True, default='example@example.com')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    street_number = models.CharField(max_length=50, blank=True, null=True)
    street_name = models.CharField(max_length=150, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    password = models.CharField(max_length=128)
    confirm_password = models.CharField(max_length=128)
    gender_choices = [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]
    gender = models.CharField(max_length=10, choices=gender_choices, blank=True, null=True, default='Male')
    created_at = models.DateTimeField(default=timezone.now)
    class Meta:
        verbose_name = "User"
        verbose_name_plural = "User"
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class CountryMultiplier(models.Model):
    COUNTRY_CHOICES = [
        ('India', 'India'),
        ('Others', 'Others'),
    ]
    country_name = models.CharField(max_length=100, unique=True, default='India', choices=COUNTRY_CHOICES)
    multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    class Meta:
        verbose_name = "Country Multiplier"
        verbose_name_plural = "Country Multiplier"
    def __str__(self):
        return f"{self.country_name} × {self.multiplier}"
    def save(self, *args, **kwargs):
        if not self.pk and CountryMultiplier.objects.count() >= 2:
            return
        super().save(*args, **kwargs)

class EnhancedWishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    product = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        # unique_together = ('user', 'content_type', 'object_id')  # TEMPORARILY REMOVED
        ordering = ['-created_at']
        verbose_name = "Enhanced Wishlist Item"
        verbose_name_plural = "Enhanced Wishlist Items"
    def __str__(self):
        return f"{self.user} - {self.product}"  # product may be any type

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist', default=1)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    product = GenericForeignKey('content_type', 'object_id')
    added_at = models.DateTimeField(default=timezone.now)
    class Meta:
        verbose_name = "Wishlist"
        verbose_name_plural = "Wishlist"
    def __str__(self):
        return f"{self.user} - {self.product}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart', default=1)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    product = GenericForeignKey('content_type', 'object_id')
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(default=timezone.now)
    class Meta:
        verbose_name = "Cart"
        verbose_name_plural = "Cart"
    def __str__(self):
        return f"{self.user} - {self.product} ({self.quantity})"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', default=1)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    product = GenericForeignKey('content_type', 'object_id')
    quantity = models.PositiveIntegerField(default=1)
    ordered_at = models.DateTimeField(default=timezone.now)
    status_choices = [('Pending', 'Pending'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')]
    status = models.CharField(max_length=20, choices=status_choices, default='Pending')
    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Order"
    def __str__(self):
        return f"{self.user} - {self.product} ({self.status})"

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', default=1)
    payment_method_choices = [('UPI', 'UPI'), ('Card', 'Card'), ('NetBanking', 'NetBanking'), ('Cash', 'Cash')]
    payment_method = models.CharField(max_length=20, choices=payment_method_choices, default='UPI')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    payment_status_choices = [('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed')]
    payment_status = models.CharField(max_length=20, choices=payment_status_choices, default='Pending')
    paid_at = models.DateTimeField(default=timezone.now)
    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payment"
    def __str__(self):
        return f"{self.order} - {self.payment_status}"

class Review(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    product = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', default=1)
    heading = models.CharField(max_length=200, default='Review Heading')
    description = models.TextField(blank=True, null=True, default='')
    image = models.ImageField(upload_to='review_images/', blank=True, null=True)
    star_rating = models.PositiveSmallIntegerField(default=5)
    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Review"
    def __str__(self):
        return f"{self.product} - {self.user} ({self.star_rating}★)"

class CarouselSlider(models.Model):
    image = models.ImageField(upload_to='carousel_images/', blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True, default='Carousel Title')
    title_color = models.CharField(max_length=7, default="#2d5a3d", blank=True, null=True)
    subtitle = models.CharField(max_length=300, blank=True, null=True, default='Carousel Subtitle')
    subtitle_color = models.CharField(max_length=7, default="#4b5563", blank=True, null=True)
    button_name = models.CharField(max_length=100, blank=True, null=True, default='Click Here')
    button_link = models.CharField(max_length=200, blank=True, null=True, default='/new-arrivals/')
    button_color = models.CharField(max_length=7, default="#2d5a3d", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Carousel Slider"
        verbose_name_plural = "Carousel Slider"
        ordering = ['order', '-created_at']
    def __str__(self):
        return self.title or f"Slider {self.id}"

class PasswordResetOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    class Meta:
        verbose_name = "Password Reset OTP"
        verbose_name_plural = "Password Reset OTPs"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.otp:
            self.otp = ''.join(random.choices(string.digits, k=6))
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()
    
    def __str__(self):
        return f"OTP for {self.email} - {self.otp}"
