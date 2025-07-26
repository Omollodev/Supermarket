from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render, redirect

def landing_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', landing_page, name='landing'),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('attendance.urls')),
    path('billing/', include('billing.urls')),
    path('inventory/', include('inventory.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
