from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.forms import ProfileUpdateForm


@login_required
def dashboard_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            user.first_name = form.cleaned_data.get('first_name', '').strip()
            user.last_name = form.cleaned_data.get('last_name', '').strip()
            user.email = form.cleaned_data.get('email', '').strip()
            user.save()
            profile_instance = form.save(commit=False)
            profile_instance.user = user
            profile_instance.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard:index')
    else:
        form = ProfileUpdateForm(
            instance=profile,
            initial={
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
            },
        )

    return render(request, 'dashboard/dashboard.html', {
        'form': form,
        'profile': profile,
    })
