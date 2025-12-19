from django.db import models

class ActiveCategoryManager(models.Manager):
    """Manager to filter products by active categories and subcategories"""
    
    def get_queryset(self):
        return super().get_queryset().filter(
            is_active=True,
            category__is_active=True,
            subcategory__is_active=True
        )

class ActiveCategoryQuerySet(models.QuerySet):
    """QuerySet with active category filtering methods"""
    
    def active_only(self):
        """Filter products with active categories and subcategories"""
        return self.filter(
            is_active=True,
            category__is_active=True,
            subcategory__is_active=True
        )
    
    def with_active_categories(self):
        """Include category and subcategory data with active filtering"""
        return self.select_related('category', 'subcategory').filter(
            category__is_active=True,
            subcategory__is_active=True
        )

class ProductManager(models.Manager):
    """Enhanced manager for product models"""
    
    def get_queryset(self):
        return ActiveCategoryQuerySet(self.model, using=self._db).active_only()
    
    def all_products(self):
        """Get all products including inactive (bypass active filtering)"""
        return ActiveCategoryQuerySet(self.model, using=self._db)
    
    def active(self):
        """Get only active products with active categories"""
        return self.get_queryset()
    
    def featured(self):
        """Get featured products with active categories"""
        return self.get_queryset().filter(is_featured=True)
    
    def by_category(self, category_name):
        """Get products by category name (only active)"""
        return self.get_queryset().filter(category__name__iexact=category_name)
    
    def by_subcategory(self, subcategory_name):
        """Get products by subcategory name (only active)"""
        return self.get_queryset().filter(subcategory__name__iexact=subcategory_name)
