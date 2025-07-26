from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from decimal import Decimal
import uuid

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'customer'

class Invoice(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Payment'),
        ('qr', 'QR Code'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    invoice_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    staff_member = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=8.25)  # Tax percentage
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, blank=True)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Calculate totals
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        
        # Update payment status
        if self.paid_amount >= self.total_amount:
            self.payment_status = 'paid'
        elif self.paid_amount > 0:
            self.payment_status = 'partial'
        elif self.due_date < timezone.now() and self.payment_status == 'pending':
            self.payment_status = 'overdue'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name if self.customer else 'Walk-in Customer'}"
    
    class Meta:
        db_table = 'invoice'
        ordering = ['-created_at']

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        
        # Update invoice subtotal
        self.invoice.subtotal = sum(item.total_price for item in self.invoice.items.all())
        self.invoice.save()
    
    def __str__(self):
        return f"{self.description} - {self.invoice.invoice_number}"
    
    class Meta:
        db_table = 'invoice_item'

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Payment'),
        ('qr', 'QR Code'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    invoice = models.ForeignKey(Invoice, related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update invoice paid amount
        total_paid = sum(payment.amount for payment in self.invoice.payments.all())
        self.invoice.paid_amount = total_paid
        self.invoice.save()
    
    def __str__(self):
        return f"Payment {self.amount} for {self.invoice.invoice_number}"
    
    class Meta:
        db_table = 'payment'

class AccountsReceivable(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateTimeField()
    is_settled = models.BooleanField(default=False)
    settled_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"AR - {self.customer.name} - {self.amount_due}"
    
    class Meta:
        db_table = 'accounts_receivable'

class AccountsPayable(models.Model):
    staff_member = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.CharField(max_length=200)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateTimeField()
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"AP - {self.staff_member.username} - {self.amount_due}"
    
    class Meta:
        db_table = 'accounts_payable'
