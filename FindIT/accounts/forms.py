from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class SignupForm(forms.Form):
    full_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your full name', 'class': 'form-input'}),
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Enter username', 'class': 'form-input'}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter email (optional)', 'class': 'form-input'}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-input password-input'}),
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-input password-input'}),
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data


class ProfileUpdateForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Full name'}),
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email address'}),
    )
    current_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Current password'}),
    )
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'New password'}),
    )
    confirm_new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm new password'}),
    )

    def __init__(self, *args, user=None, profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.profile = profile

        if self.user and not self.is_bound:
            profile_name = self.profile.full_name if self.profile else ''
            self.initial.update({
                'full_name': profile_name,
                'username': self.user.username,
                'email': self.user.email,
            })

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.exclude(pk=self.user.pk).filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get('current_password', '')
        new_password = cleaned_data.get('new_password', '')
        confirm_new_password = cleaned_data.get('confirm_new_password', '')

        any_password_input = any([current_password, new_password, confirm_new_password])
        if any_password_input:
            if not current_password:
                self.add_error('current_password', 'Current password is required to change password.')
            elif not self.user.check_password(current_password):
                self.add_error('current_password', 'Current password is incorrect.')

            if not new_password:
                self.add_error('new_password', 'Please enter a new password.')
            elif new_password != confirm_new_password:
                self.add_error('confirm_new_password', 'New passwords do not match.')
            else:
                validate_password(new_password, self.user)

        return cleaned_data

    def save(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        self.profile.full_name = full_name
        self.profile.save(update_fields=['full_name'])

        self.user.username = self.cleaned_data.get('username', '').strip()
        self.user.email = self.cleaned_data.get('email', '').strip()
        self.user.save(update_fields=['username', 'email'])

        new_password = self.cleaned_data.get('new_password', '')
        if new_password:
            self.user.set_password(new_password)
            self.user.save()

        return self.user
