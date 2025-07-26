from django.contrib import admin
from .models import Attendance, WageSummary

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'clock_in', 'clock_out', 'total_hours', 'wage_earned')
    list_filter = ('date', 'user__role')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('total_hours', 'wage_earned')
    date_hierarchy = 'date'

@admin.register(WageSummary)
class WageSummaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'year', 'total_hours', 'total_wage', 'is_paid', 'paid_date')
    list_filter = ('year', 'month', 'is_paid', 'user__role')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('total_hours', 'total_wage')
