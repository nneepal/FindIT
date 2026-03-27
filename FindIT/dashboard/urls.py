from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='index'),
    path('admin/', views.admin_dashboard_view, name='admin-dashboard-local'),
    path('admin/stats/', views.admin_stats_api, name='admin-stats-local'),
]
