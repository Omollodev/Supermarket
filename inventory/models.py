from django.db import models
from django.utils import timezone
from accounts.models import CustomUser

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'category'
        verbose_name_plural = 'Categories'

class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_in_stock = models.IntegerField(default=0)
    minimum_stock_level = models.IntegerField(default=10)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.minimum_stock_level
    
    @property
    def profit_margin(self):
        if self.cost_price > 0:
            return ((self.unit_price - self.cost_price) / self.cost_price) * 100
        return 0
    
    class Meta:
        db_table = 'product'
        ordering = ['name']
