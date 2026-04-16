from django.contrib import admin
from .models import Attendance, WageSummary, MpesaPayout

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


@admin.register(MpesaPayout)
class MpesaPayoutAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    list_display = (
        'user', 'month', 'year', 'amount', 'status', 'phone',
        'conversation_id', 'created_at',
    )
    list_filter = ('status', 'year', 'month')
    search_fields = ('user__username', 'conversation_id', 'transaction_id', 'phone')
    readonly_fields = (
        'user', 'wage_summary', 'amount', 'phone', 'month', 'year',
        'conversation_id', 'originator_conversation_id',
        'result_code', 'result_desc', 'transaction_id', 'receipt',
        'initiated_by', 'raw_result', 'created_at', 'updated_at',
    )
