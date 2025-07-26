from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db import models
from .models import Product, Category

@login_required
def inventory_dashboard(request):
    total_products = Product.objects.filter(is_active=True).count()
    low_stock_products = Product.objects.filter(
        is_active=True,
        quantity_in_stock__lte=models.F('minimum_stock_level')
    ).count()
    
    context = {
        'total_products': total_products,
        'low_stock_products': low_stock_products,
    }
    
    return render(request, 'inventory/dashboard.html', context)

@login_required
def product_list(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'inventory/product_list.html', {'products': products})

@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})
