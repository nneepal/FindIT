from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import BadHeaderError

from .forms import ExistingEmailPasswordResetForm, SignupForm
from .models import PasswordResetRequest


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core:index')

    form = SignupForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            full_name = form.cleaned_data['full_name'].strip()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data.get('email', '').strip().lower()

            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
            )
            user.profile.full_name = full_name
            user.profile.save(update_fields=['full_name'])
            login(request, user)
            messages.success(request, f'Welcome to FINDIT, {full_name or username}!')
            return redirect('core:index')

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:index')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', '')
            return redirect(next_url if next_url else 'core:index')
        else:
            error = 'Invalid username or password. Please try again.'

    return render(request, 'accounts/login.html', {'error': error})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:index')


class CustomPasswordResetView(PasswordResetView):
    form_class = ExistingEmailPasswordResetForm
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.txt'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')

    def _get_client_ip(self):
        forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR', '')

    def form_valid(self, form):
        email = form.cleaned_data.get('email', '').strip()
        users = list(form.get_users(email))
        try:
            response = super().form_valid(form)
        except Exception as exc:
            PasswordResetRequest.objects.create(
                user=users[0] if users else None,
                email=email,
                sent_successfully=False,
                ip_address=self._get_client_ip(),
                user_agent=(self.request.META.get('HTTP_USER_AGENT', '') or '')[:255],
            )
            if isinstance(exc, (BadHeaderError, ConnectionError, OSError)):
                error_message = 'Unable to send reset email right now. Please try again in a few minutes.'
            else:
                error_message = 'Reset email could not be sent. Check email configuration and try again.'
            form.add_error(None, error_message)
            return self.render_to_response(self.get_context_data(form=form))

        PasswordResetRequest.objects.create(
            user=users[0] if users else None,
            email=email,
            sent_successfully=bool(users),
            ip_address=self._get_client_ip(),
            user_agent=(self.request.META.get('HTTP_USER_AGENT', '') or '')[:255],
        )
        return response

    def form_invalid(self, form):
        email = (form.data.get('email') or '').strip()
        PasswordResetRequest.objects.create(
            user=None,
            email=email,
            sent_successfully=False,
            ip_address=self._get_client_ip(),
            user_agent=(self.request.META.get('HTTP_USER_AGENT', '') or '')[:255],
        )
        return super().form_invalid(form)
