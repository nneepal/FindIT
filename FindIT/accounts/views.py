from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignupForm


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('core:index')

    form = SignupForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            full_name = form.cleaned_data['full_name'].strip()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            email = form.cleaned_data.get('email', '')

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
