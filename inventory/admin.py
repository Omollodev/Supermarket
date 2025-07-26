from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'sku', 'unit_price', 'quantity_in_stock', 'is_low_stock', 'is_active')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'barcode')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('unit_price', 'quantity_in_stock', 'is_active')
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock'
