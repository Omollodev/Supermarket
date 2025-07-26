from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Attendance, WageSummary
from accounts.models import CustomUser
import json

@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()
    
    # Get today's attendance
    today_attendance = Attendance.objects.filter(user=user, date=today).first()
    
    # Get recent attendance records
    recent_attendance = Attendance.objects.filter(user=user).order_by('-date')[:10]
    
    # Calculate this month's stats
    current_month = timezone.now().month
    current_year = timezone.now().year
    
    monthly_stats = Attendance.objects.filter(
        user=user,
        date__month=current_month,
        date__year=current_year
    ).aggregate(
        total_hours=Sum('total_hours'),
        total_wage=Sum('wage_earned')
    )
    
    context = {
        'today_attendance': today_attendance,
        'recent_attendance': recent_attendance,
        'monthly_stats': monthly_stats,
        'user': user,
    }
    
    return render(request, 'attendance/dashboard.html', context)

@login_required
def clock_in_view(request):
    user = request.user
    today = timezone.now().date()
    
    # Check if user already clocked in today
    existing_attendance = Attendance.objects.filter(user=user, date=today, clock_out__isnull=True).first()
    
    if existing_attendance:
        messages.warning(request, 'You are already clocked in!')
    else:
        Attendance.objects.create(
            user=user,
            clock_in=timezone.now()
        )
        messages.success(request, 'Successfully clocked in!')
    
    return redirect('dashboard')

@login_required
def clock_out_view(request):
    user = request.user
    today = timezone.now().date()
    
    # Find today's attendance record without clock_out
    attendance = Attendance.objects.filter(user=user, date=today, clock_out__isnull=True).first()
    
    if attendance:
        attendance.clock_out = timezone.now()
        attendance.save()
        messages.success(request, f'Successfully clocked out! You worked {attendance.total_hours} hours today.')
    else:
        messages.error(request, 'No active clock-in found for today!')
    
    return redirect('dashboard')

@login_required
def attendance_history_view(request):
    user = request.user
    
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    attendance_records = Attendance.objects.filter(user=user)
    
    if start_date:
        attendance_records = attendance_records.filter(date__gte=start_date)
    if end_date:
        attendance_records = attendance_records.filter(date__lte=end_date)
    
    attendance_records = attendance_records.order_by('-date')
    
    # Calculate totals
    totals = attendance_records.aggregate(
        total_hours=Sum('total_hours'),
        total_wage=Sum('wage_earned')
    )
    
    context = {
        'attendance_records': attendance_records,
        'totals': totals,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'attendance/history.html', context)

@login_required
def wage_summary_view(request):
    user = request.user
    
    # Get or create wage summaries for the last 12 months
    wage_summaries = []
    current_date = timezone.now().date()
    
    for i in range(12):
        month = current_date.month
        year = current_date.year
        
        # Calculate monthly totals
        monthly_attendance = Attendance.objects.filter(
            user=user,
            date__month=month,
            date__year=year
        ).aggregate(
            total_hours=Sum('total_hours'),
            total_wage=Sum('wage_earned')
        )
        
        # Get or create wage summary
        wage_summary, created = WageSummary.objects.get_or_create(
            user=user,
            month=month,
            year=year,
            defaults={
                'total_hours': monthly_attendance['total_hours'] or 0,
                'total_wage': monthly_attendance['total_wage'] or 0,
            }
        )
        
        if not created:
            # Update existing summary
            wage_summary.total_hours = monthly_attendance['total_hours'] or 0
            wage_summary.total_wage = monthly_attendance['total_wage'] or 0
            wage_summary.save()
        
        wage_summaries.append(wage_summary)
        
        # Move to previous month
        if current_date.month == 1:
            current_date = current_date.replace(year=current_date.year - 1, month=12)
        else:
            current_date = current_date.replace(month=current_date.month - 1)
    
    context = {
        'wage_summaries': wage_summaries,
    }
    
    return render(request, 'attendance/wage_summary.html', context)

# Manager/Admin views
@login_required
def staff_attendance_view(request):
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'Access denied!')
        return redirect('dashboard')
    
    staff_users = CustomUser.objects.filter(role='staff')
    today = timezone.now().date()
    
    staff_attendance = []
    for staff in staff_users:
        attendance = Attendance.objects.filter(user=staff, date=today).first()
        staff_attendance.append({
            'user': staff,
            'attendance': attendance,
            'is_clocked_in': attendance and not attendance.clock_out if attendance else False
        })
    
    context = {
        'staff_attendance': staff_attendance,
        'today': today,
    }
    
    return render(request, 'attendance/staff_attendance.html', context)
