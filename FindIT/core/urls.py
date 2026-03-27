from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_item, name='search'),
    path('report/', views.report_item, name='report'),
    path('listed-items/', views.listed_items, name='listed-items'),
    path('pending-complaints/', views.pending_complaints, name='pending-complaints'),
    path('claim-found-item/<int:item_id>/', views.claim_found_item, name='claim-found-item'),
]
