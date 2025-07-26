from django.urls import path
from . import views

urlpatterns = [
    path('', views.billing_dashboard, name='billing_dashboard'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/edit/', views.edit_invoice, name='edit_invoice'),
    path('invoices/<int:invoice_id>/payment/', views.add_payment, name='add_payment'),
    path('invoices/<int:invoice_id>/receipt/', views.generate_receipt, name='generate_receipt'),
    path('items/<int:item_id>/delete/', views.delete_invoice_item, name='delete_invoice_item'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.create_customer, name='create_customer'),
    path('accounts-receivable/', views.accounts_receivable_view, name='accounts_receivable'),
    path('accounts-payable/', views.accounts_payable_view, name='accounts_payable'),
]
