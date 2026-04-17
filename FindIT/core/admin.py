from django.contrib import admin
from .models import FoundItem, LostItem, Notification


@admin.register(FoundItem)
class FoundItemAdmin(admin.ModelAdmin):
	list_display = ('id', 'item_name', 'category', 'location_found', 'date_found', 'is_valuable', 'reported_by', 'created_at')
	list_filter = ('category', 'location_found', 'condition', 'is_valuable', 'created_at')
	search_fields = ('item_name', 'description', 'reported_by__username')


@admin.register(LostItem)
class LostItemAdmin(admin.ModelAdmin):
	list_display = ('id', 'item_name', 'category', 'condition', 'location_lost', 'date_lost', 'searched_by', 'created_at')
	list_filter = ('category', 'condition', 'location_lost', 'created_at')
	search_fields = ('item_name', 'description', 'searched_by__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
	list_display = ('id', 'recipient', 'title', 'is_read', 'created_at')
	list_filter = ('is_read', 'created_at')
	search_fields = ('recipient__username', 'title', 'message')
