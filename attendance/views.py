from urllib.parse import urlencode

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from datetime import datetime, timedelta
from decimal import Decimal
import json
import logging

from .models import Attendance, WageSummary, MpesaPayout
from . import mpesa as mpesa_client
from accounts.models import CustomUser

logger = logging.getLogger(__name__)


def _wage_payouts_redirect(month: int, year: int):
    q = urlencode({'month': month, 'year': year})
    return redirect(f'{reverse("wage_payouts")}?{q}')


@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()

    today_rows = Attendance.objects.filter(user=user, date=today)
    # Same rule as clock_in / clock_out: one open shift per day
    active_shift = today_rows.filter(clock_out__isnull=True).order_by('-clock_in').first()

    completed_hours = today_rows.aggregate(h=Sum('total_hours'))['h'] or Decimal('0')
    hours_today = completed_hours
    if active_shift:
        delta = timezone.now() - active_shift.clock_in
        hours_today += Decimal(str(round(delta.total_seconds() / 3600, 2)))
    
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
        'active_shift': active_shift,
        'hours_today': hours_today,
        'recent_attendance': recent_attendance,
        'monthly_stats': monthly_stats,
        'user': user,
    }
    
    return render(request, 'attendance/dashboard.html', context)

@login_required
def clock_in_view(request):
    user = request.user
    today = timezone.now().date()

    if user.role == 'staff' and not (user.mpesa_phone or '').strip():
        messages.warning(
            request,
            'Add your M-Pesa phone number in Profile before you can clock in.',
        )
        return redirect('profile')
    
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
        
        # Move to previous month (use 1st + timedelta to avoid invalid days e.g. Mar 31 -> Feb)
        first_of_month = current_date.replace(day=1)
        current_date = first_of_month - timedelta(days=1)
    
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


def _refresh_wage_summary(user, month, year):
    monthly = Attendance.objects.filter(
        user=user,
        date__month=month,
        date__year=year,
    ).aggregate(
        total_hours=Sum('total_hours'),
        total_wage=Sum('wage_earned'),
    )
    wage_summary, _ = WageSummary.objects.get_or_create(
        user=user,
        month=month,
        year=year,
        defaults={
            'total_hours': monthly['total_hours'] or Decimal('0'),
            'total_wage': monthly['total_wage'] or Decimal('0'),
        },
    )
    wage_summary.total_hours = monthly['total_hours'] or Decimal('0')
    wage_summary.total_wage = monthly['total_wage'] or Decimal('0')
    wage_summary.save(
        update_fields=['total_hours', 'total_wage'],
    )
    return wage_summary


@login_required
def wage_payouts_view(request):
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'Access denied!')
        return redirect('dashboard')

    now = timezone.now()
    try:
        month = int(request.GET.get('month', now.month))
        year = int(request.GET.get('year', now.year))
    except (TypeError, ValueError):
        month, year = now.month, now.year

    staff_list = CustomUser.objects.filter(role='staff').order_by('username')
    rows = []
    for staff in staff_list:
        ws = _refresh_wage_summary(staff, month, year)
        blocking = MpesaPayout.objects.filter(
            user=staff,
            month=month,
            year=year,
            status=MpesaPayout.Status.QUEUED,
        ).exists()
        rows.append({
            'user': staff,
            'wage_summary': ws,
            'payout_pending': blocking,
            'last_payout': MpesaPayout.objects.filter(
                user=staff, month=month, year=year,
            ).order_by('-created_at').first(),
        })

    mpesa_ready = True
    try:
        mpesa_client.assert_mpesa_b2c_configured()
    except mpesa_client.MpesaConfigError:
        mpesa_ready = False

    context = {
        'rows': rows,
        'month': month,
        'year': year,
        'mpesa_ready': mpesa_ready,
    }
    return render(request, 'attendance/wage_payouts.html', context)


@login_required
@require_POST
def initiate_wage_mpesa_payout(request):
    if request.user.role not in ['admin', 'manager']:
        messages.error(request, 'Access denied!')
        return redirect('dashboard')

    try:
        user_id = int(request.POST.get('user_id', ''))
        month = int(request.POST.get('month', ''))
        year = int(request.POST.get('year', ''))
    except (TypeError, ValueError):
        messages.error(request, 'Invalid payout request.')
        return redirect('wage_payouts')

    staff = get_object_or_404(CustomUser, pk=user_id, role='staff')
    wage_summary = _refresh_wage_summary(staff, month, year)

    if wage_summary.is_paid:
        messages.info(request, f'{staff.username} is already marked paid for {month}/{year}.')
        return _wage_payouts_redirect(month, year)

    if MpesaPayout.objects.filter(
        user=staff,
        month=month,
        year=year,
        status=MpesaPayout.Status.QUEUED,
    ).exists():
        messages.warning(
            request,
            'A payout is already in progress for this period. Wait for the M-Pesa callback.',
        )
        return _wage_payouts_redirect(month, year)

    phone = (staff.mpesa_phone or '').strip()
    if not phone:
        messages.error(
            request,
            f'{staff.username} has no M-Pesa number on file. Ask them to add it in Profile.',
        )
        return _wage_payouts_redirect(month, year)

    try:
        amount_kes = mpesa_client.mpesa_amount_to_int(wage_summary.total_wage)
    except ValueError as exc:
        messages.error(request, str(exc))
        return _wage_payouts_redirect(month, year)

    payout = MpesaPayout.objects.create(
        user=staff,
        wage_summary=wage_summary,
        amount=wage_summary.total_wage,
        phone=phone,
        month=month,
        year=year,
        status=MpesaPayout.Status.PENDING,
        initiated_by=request.user,
    )

    remarks = f'Wage {year}-{month:02d} {staff.username}'[:255]
    try:
        data = mpesa_client.initiate_b2c_payment(
            phone=phone,
            amount_kes=amount_kes,
            remarks=remarks,
        )
    except (mpesa_client.MpesaConfigError, mpesa_client.MpesaAPIError, OSError) as exc:
        logger.exception('M-Pesa B2C initiate failed')
        payout.status = MpesaPayout.Status.FAILED
        payout.result_desc = str(exc)
        payout.save(update_fields=['status', 'result_desc', 'updated_at'])
        messages.error(request, f'M-Pesa request failed: {exc}')
        return _wage_payouts_redirect(month, year)

    resp_code = str(data.get('ResponseCode', ''))
    if resp_code != '0':
        payout.status = MpesaPayout.Status.FAILED
        payout.result_desc = data.get('ResponseDescription', '') or json.dumps(data)
        payout.save(update_fields=['status', 'result_desc', 'updated_at'])
        messages.error(
            request,
            data.get('ResponseDescription', 'Daraja rejected the payout request.'),
        )
        return _wage_payouts_redirect(month, year)

    payout.status = MpesaPayout.Status.QUEUED
    payout.conversation_id = data.get('ConversationID', '') or ''
    payout.originator_conversation_id = data.get('OriginatorConversationID', '') or ''
    payout.save(
        update_fields=[
            'status', 'conversation_id', 'originator_conversation_id', 'updated_at',
        ],
    )
    messages.success(
        request,
        f'Payout queued for {staff.get_full_name()}. M-Pesa will complete shortly.',
    )
    return _wage_payouts_redirect(month, year)


def _apply_b2c_callback(body):
    parsed = mpesa_client.parse_b2c_result_body(body)
    cid = parsed.get('conversation_id') or ''
    oid = parsed.get('originator_conversation_id') or ''
    rc = parsed.get('result_code')
    success = rc == 0 or str(rc) == '0'

    payout = MpesaPayout.objects.filter(
        Q(conversation_id=cid) | Q(originator_conversation_id=oid),
    ).exclude(status=MpesaPayout.Status.SUCCESS).order_by('-created_at').first()

    if not payout:
        logger.warning('M-Pesa B2C callback: no matching payout for %s / %s', cid, oid)
        return

    payout.result_code = parsed.get('result_code_str') or str(rc or '')
    payout.result_desc = parsed.get('result_desc', '')[:2000]
    payout.transaction_id = parsed.get('transaction_id', '') or ''
    payout.receipt = parsed.get('receipt', '') or ''
    payout.raw_result = json.dumps(body)[:8000]
    payout.status = MpesaPayout.Status.SUCCESS if success else MpesaPayout.Status.FAILED
    payout.save()

    if success and payout.wage_summary_id:
        ws = payout.wage_summary
        ws.is_paid = True
        ws.paid_date = timezone.now()
        ws.save(update_fields=['is_paid', 'paid_date'])


@csrf_exempt
@require_http_methods(['POST'])
def mpesa_b2c_result_webhook(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HttpResponse('Bad Request', status=400)
    try:
        _apply_b2c_callback(body)
    except Exception:
        logger.exception('M-Pesa B2C result handler error')
    return HttpResponse('OK')


@csrf_exempt
@require_http_methods(['POST'])
def mpesa_b2c_timeout_webhook(request):
    try:
        body = json.loads(request.body.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HttpResponse('Bad Request', status=400)
    try:
        parsed = mpesa_client.parse_b2c_result_body(body)
        cid = parsed.get('conversation_id') or ''
        oid = parsed.get('originator_conversation_id') or ''
        payout = MpesaPayout.objects.filter(
            Q(conversation_id=cid) | Q(originator_conversation_id=oid),
        ).exclude(status=MpesaPayout.Status.SUCCESS).order_by('-created_at').first()
        if payout and payout.status == MpesaPayout.Status.QUEUED:
            payout.status = MpesaPayout.Status.FAILED
            payout.result_desc = 'Queue timeout — retry payout if funds were not sent.'
            payout.raw_result = json.dumps(body)[:8000]
            payout.save()
    except Exception:
        logger.exception('M-Pesa B2C timeout handler error')
    return HttpResponse('OK')
