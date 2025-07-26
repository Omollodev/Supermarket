from django.contrib import admin
from .models import Customer, Invoice, InvoiceItem, Payment, AccountsReceivable, AccountsPayable

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('created_at',)

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ('total_price',)

class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_date',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'staff_member', 'total_amount', 'payment_status', 'created_at')
    list_filter = ('payment_status', 'payment_method', 'created_at')
    search_fields = ('invoice_number', 'customer__name', 'staff_member__username')
    readonly_fields = ('invoice_number', 'subtotal', 'tax_amount', 'total_amount')
    inlines = [InvoiceItemInline, PaymentInline]
    date_hierarchy = 'created_at'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'amount', 'payment_method', 'payment_date')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('invoice__invoice_number', 'transaction_id')

@admin.register(AccountsReceivable)
class AccountsReceivableAdmin(admin.ModelAdmin):
    list_display = ('customer', 'invoice', 'amount_due', 'due_date', 'is_settled')
    list_filter = ('is_settled', 'due_date')
    search_fields = ('customer__name', 'invoice__invoice_number')

@admin.register(AccountsPayable)
class AccountsPayableAdmin(admin.ModelAdmin):
    list_display = ('staff_member', 'description', 'amount_due', 'due_date', 'is_paid')
    list_filter = ('is_paid', 'due_date')
    search_fields = ('staff_member__username', 'description')
