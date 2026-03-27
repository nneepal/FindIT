from django.contrib import admin
from .models import AdminManagedItem


@admin.register(AdminManagedItem)
class AdminManagedItemAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'location', 'created_at')
	search_fields = ('title', 'category', 'location')
