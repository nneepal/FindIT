from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_item, name='search'),
    path('report/', views.report_item, name='report'),
]
