from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from attendance.mpesa import normalize_mpesa_msisdn
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    mpesa_phone = forms.CharField(
        max_length=15,
        required=False,
        help_text='M-Pesa number for salary (e.g. 0712345678). Required before clock-in as staff.',
    )
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    
    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'mpesa_phone', 'address', 'password1', 'password2',
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def clean_mpesa_phone(self):
        raw = (self.cleaned_data.get('mpesa_phone') or '').strip()
        if not raw:
            return ''
        try:
            return normalize_mpesa_msisdn(raw)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = (
            'first_name', 'last_name', 'email', 'phone_number', 'mpesa_phone',
            'address', 'profile_picture',
        )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'profile_picture':
                field.widget.attrs['class'] = 'form-control'
            else:
                field.widget.attrs['class'] = 'form-control-file'
        self.fields['mpesa_phone'].help_text = (
            'Safaricom M-Pesa number for wage payouts (2547… or 07…).'
        )

    def clean_mpesa_phone(self):
        raw = (self.cleaned_data.get('mpesa_phone') or '').strip()
        if not raw:
            return ''
        try:
            return normalize_mpesa_msisdn(raw)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )

class PasswordResetForm(forms.Form):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New Password'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        
        return cleaned_data
