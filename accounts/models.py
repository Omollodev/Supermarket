from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

# General contact; Kenyan format preferred (0… or 254…).
_phone_validator = RegexValidator(
    regex=r"^\+?254\d{9}$|^0\d{9}$|^$",
    message="Enter a valid Kenyan phone (e.g. 0712345678 or +254712345678).",
)

# M-Pesa payout number: international format without +.
_mpesa_validator = RegexValidator(
    regex=r"^$|^254[17]\d{8}$",
    message="M-Pesa number must be 2547XXXXXXXX or 2541XXXXXXXX.",
)

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    phone_number = models.CharField(
        max_length=15,
        validators=[_phone_validator],
        blank=True,
        help_text="Contact phone (e.g. 0712345678).",
    )
    mpesa_phone = models.CharField(
        max_length=12,
        blank=True,
        validators=[_mpesa_validator],
        help_text="Number registered on M-Pesa for salary payouts (2547XXXXXXXX).",
    )
    address = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=15.00)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    class Meta:
        db_table = 'custom_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

class PasswordResetToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Password reset token for {self.user.username}"
    
    class Meta:
        db_table = 'password_reset_token'
