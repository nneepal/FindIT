from django import forms

from .models import AdminManagedItem


class AdminManagedItemForm(forms.ModelForm):
    class Meta:
        model = AdminManagedItem
        fields = ['title', 'category', 'location']
