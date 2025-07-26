from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('clock-in/', views.clock_in_view, name='clock_in'),
    path('clock-out/', views.clock_out_view, name='clock_out'),
    path('history/', views.attendance_history_view, name='attendance_history'),
    path('wages/', views.wage_summary_view, name='wage_summary'),
    path('staff/', views.staff_attendance_view, name='staff_attendance'),
]
