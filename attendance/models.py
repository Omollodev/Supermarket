from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from datetime import datetime, timedelta
from decimal import Decimal

class Attendance(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    clock_in = models.DateTimeField()
    clock_out = models.DateTimeField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    total_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    wage_earned = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if self.clock_out:
            # Calculate total hours
            time_diff = self.clock_out - self.clock_in
            hours_float = time_diff.total_seconds() / 3600
            self.total_hours = Decimal(str(round(hours_float, 2)))
            # Calculate wage - ensure both values are Decimal
            self.wage_earned = self.total_hours * self.user.hourly_rate
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    class Meta:
        db_table = 'attendance'
        ordering = ['-date', '-clock_in']

class WageSummary(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    month = models.IntegerField()
    year = models.IntegerField()
    total_hours = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
    total_wage = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.month}/{self.year}"
    
    class Meta:
        db_table = 'wage_summary'
        unique_together = ['user', 'month', 'year']
