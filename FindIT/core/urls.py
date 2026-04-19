from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('search/', views.search_item, name='search'),
    path('search/detect-category/', views.detect_search_category, name='detect-search-category'),
    path('report/', views.report_item, name='report'),
    path('report/detect-category/', views.detect_report_category, name='detect-report-category'),
    path('listed-items/', views.listed_items, name='listed-items'),
    path('listed-items/ai-match/<int:item_id>/', views.ai_match_lost_item, name='ai-match-lost-item'),
    path('pending-complaints/', views.pending_complaints, name='pending-complaints'),
    path('claim-found-item/<int:item_id>/', views.claim_found_item, name='claim-found-item'),
    path('verify-claim/<int:claim_id>/', views.verify_claim, name='verify-claim'),
]
