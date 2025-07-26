from django.urls import path
from . import views

urlpatterns = [
    path('', views.inventory_dashboard, name='inventory_dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('categories/', views.category_list, name='category_list'),
]
