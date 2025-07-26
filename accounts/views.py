from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.crypto import get_random_string
from .forms import CustomUserCreationForm, CustomAuthenticationForm, ProfileUpdateForm, PasswordResetRequestForm, PasswordResetForm
from .models import CustomUser, PasswordResetToken

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                return redirect('dashboard')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})

def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = CustomUser.objects.get(email=email)
                token = get_random_string(50)
                PasswordResetToken.objects.create(user=user, token=token)
                
                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'token': token})
                )
                
                send_mail(
                    'Password Reset Request',
                    f'Click the following link to reset your password: {reset_url}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, 'Password reset email sent!')
                return redirect('login')
            except CustomUser.DoesNotExist:
                messages.error(request, 'No user found with this email address.')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'accounts/password_reset_request.html', {'form': form})

def password_reset_confirm(request, token):
    reset_token = get_object_or_404(PasswordResetToken, token=token, is_used=False)
    
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password1']
            user = reset_token.user
            user.set_password(password)
            user.save()
            reset_token.is_used = True
            reset_token.save()
            messages.success(request, 'Password reset successfully!')
            return redirect('login')
    else:
        form = PasswordResetForm()
    
    return render(request, 'accounts/password_reset_confirm.html', {'form': form})
