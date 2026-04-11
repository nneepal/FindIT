from functools import wraps

from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from accounts.forms import ProfileUpdateForm
from accounts.models import UserProfile
from core.forms import FoundItemReportForm, LostItemSearchForm
from core.models import ClaimVerification, FoundItem, FoundItemClaim, LostItem


@login_required
def dashboard_view(request):
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, user=user, profile=profile)
        if form.is_valid():
            updated_user = form.save()
            if form.cleaned_data.get('new_password'):
                update_session_auth_hash(request, updated_user)
                messages.success(request, 'Your profile and password have been updated successfully!')
            else:
                messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard:index')
    else:
        form = ProfileUpdateForm(user=user, profile=profile)

    claimed_items = FoundItemClaim.objects.filter(claimed_by=user).select_related('found_item').order_by('-created_at')
    verification_requests = ClaimVerification.objects.filter(claimed_by=user).select_related(
        'found_item',
        'claim',
    ).order_by('-submitted_at')

    return render(request, 'dashboard/dashboard.html', {
        'form': form,
        'profile': profile,
        'claimed_items': claimed_items,
        'verification_requests': verification_requests,
    })


def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'You do not have permission to access the admin dashboard.')
            return redirect('core:index')
        return view_func(request, *args, **kwargs)

    return _wrapped


def _get_admin_stats():
    found_count = FoundItem.objects.count()
    lost_count = LostItem.objects.count()
    total_listed_items = found_count + lost_count
    active_users = User.objects.filter(is_active=True).count()
    recovery_rate = round((found_count / total_listed_items) * 100) if total_listed_items else 0

    return {
        'total_listed_items': total_listed_items,
        'found_reports': found_count,
        'lost_reports': lost_count,
        'active_users': active_users,
        'recovery_rate': f'{recovery_rate}%',
    }


@admin_required
def admin_dashboard_view(request):
    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        if action == 'add_user':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            full_name = request.POST.get('full_name', '').strip()
            is_staff = request.POST.get('is_staff') == 'on'

            if not username or not password:
                messages.error(request, 'Username and password are required to add a user.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'A user with that username already exists.')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.is_staff = is_staff
                user.save(update_fields=['is_staff'])
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.full_name = full_name
                profile.save(update_fields=['full_name'])
                messages.success(request, f'User "{username}" was added successfully.')
                return redirect('admin-dashboard')

        elif action == 'delete_user':
            user_id = request.POST.get('user_id')
            try:
                target_user = User.objects.get(pk=user_id)
                if target_user == request.user:
                    messages.error(request, 'You cannot delete your own account from this dashboard.')
                else:
                    username = target_user.username
                    target_user.delete()
                    messages.success(request, f'User "{username}" deleted successfully.')
                    return redirect('admin-dashboard')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')

        elif action == 'add_found_item':
            found_form = FoundItemReportForm(request.POST, request.FILES)
            if found_form.is_valid():
                found_item = found_form.save(commit=False)
                found_item.reported_by = request.user
                found_item.save()
                messages.success(request, 'Found item added successfully.')
                return redirect('admin-dashboard')
            messages.error(request, 'Could not add found item. Please check the details and image upload.')

        elif action == 'delete_found_item':
            item_id = request.POST.get('item_id')
            deleted_count, _ = FoundItem.objects.filter(pk=item_id).delete()
            if deleted_count:
                messages.success(request, 'Found item deleted successfully.')
                return redirect('admin-dashboard')
            messages.error(request, 'Found item not found.')

        elif action == 'add_lost_item':
            lost_form = LostItemSearchForm(request.POST, request.FILES)
            if lost_form.is_valid():
                lost_item = lost_form.save(commit=False)
                lost_item.searched_by = request.user
                lost_item.save()
                messages.success(request, 'Lost item added successfully.')
                return redirect('admin-dashboard')
            messages.error(request, 'Could not add lost item. Please check the details and image upload.')

        elif action == 'delete_lost_item':
            item_id = request.POST.get('item_id')
            deleted_count, _ = LostItem.objects.filter(pk=item_id).delete()
            if deleted_count:
                messages.success(request, 'Lost item deleted successfully.')
                return redirect('admin-dashboard')
            messages.error(request, 'Lost item not found.')

        elif action == 'review_verification':
            verification_id = request.POST.get('verification_id')
            decision = request.POST.get('decision', '').strip()
            admin_message = request.POST.get('admin_message', '').strip()

            try:
                verification = ClaimVerification.objects.select_related('found_item').get(pk=verification_id)
            except ClaimVerification.DoesNotExist:
                messages.error(request, 'Verification request not found.')
            else:
                if decision not in {'verified', 'rejected'}:
                    messages.error(request, 'Invalid verification decision.')
                else:
                    verification.status = decision
                    verification.admin_message = admin_message
                    verification.reviewed_by = request.user
                    verification.reviewed_at = timezone.now()
                    verification.save(update_fields=['status', 'admin_message', 'reviewed_by', 'reviewed_at', 'updated_at'])
                    messages.success(request, f'Verification request marked as {decision}.')
                    return redirect('admin-dashboard')

        elif action == 'close_complaint':
            verification_id = request.POST.get('verification_id')
            close_note = request.POST.get('close_note', '').strip() or 'Complaint closed by admin.'

            try:
                verification = ClaimVerification.objects.select_related('claim', 'found_item', 'claimed_by').get(pk=verification_id)
            except ClaimVerification.DoesNotExist:
                messages.error(request, 'Complaint record not found.')
            else:
                verification.status = 'closed'
                verification.admin_message = close_note
                verification.reviewed_by = request.user
                verification.reviewed_at = timezone.now()
                verification.save(update_fields=['status', 'admin_message', 'reviewed_by', 'reviewed_at', 'updated_at'])

                has_open_complaints = ClaimVerification.objects.filter(
                    found_item=verification.found_item,
                ).exclude(status='closed').exists()

                if verification.found_item.claim_status == 'claimed' and not has_open_complaints:
                    verification.found_item.claim_status = 'open'
                    verification.found_item.save(update_fields=['claim_status', 'updated_at'])

                LostItem.objects.filter(
                    searched_by=verification.claimed_by,
                    item_name__iexact=verification.found_item.item_name,
                    category=verification.found_item.category,
                    claim_status='claimed',
                ).update(claim_status='open')

                messages.success(request, 'Complaint closed and related claim status updated.')
                return redirect('admin-dashboard')

    user_query = request.GET.get('user_q', '').strip()
    found_query = request.GET.get('found_q', '').strip()
    lost_query = request.GET.get('lost_q', '').strip()

    users = User.objects.select_related('profile').order_by('-date_joined')
    if user_query:
        users = users.filter(
            Q(username__icontains=user_query)
            | Q(email__icontains=user_query)
            | Q(profile__full_name__icontains=user_query)
        )

    users = list(users)
    for listed_user in users:
        UserProfile.objects.get_or_create(user=listed_user)

    found_items = FoundItem.objects.select_related('reported_by').order_by('-created_at')
    if found_query:
        found_items = found_items.filter(
            Q(item_name__icontains=found_query)
            | Q(category__icontains=found_query)
            | Q(location_found__icontains=found_query)
        )

    lost_items = LostItem.objects.select_related('searched_by').order_by('-created_at')
    if lost_query:
        lost_items = lost_items.filter(
            Q(item_name__icontains=lost_query)
            | Q(category__icontains=lost_query)
            | Q(location_lost__icontains=lost_query)
        )

    verifications = ClaimVerification.objects.select_related(
        'claim',
        'found_item',
        'claimed_by',
        'reviewed_by',
    ).order_by('status', '-submitted_at')

    pending_complaints = verifications.exclude(status='closed')

    context = {
        'stats': _get_admin_stats(),
        'users': users,
        'found_items': found_items,
        'lost_items': lost_items,
        'found_form': FoundItemReportForm(),
        'lost_form': LostItemSearchForm(),
        'found_category_choices': FoundItem.CATEGORY_CHOICES,
        'found_location_choices': FoundItem.LOCATION_CHOICES,
        'found_condition_choices': FoundItem.CONDITION_CHOICES,
        'lost_category_choices': LostItem.CATEGORY_CHOICES,
        'lost_location_choices': LostItem.LOCATION_CHOICES,
        'lost_condition_choices': LostItem.CONDITION_CHOICES,
        'verifications': verifications,
        'pending_complaints': pending_complaints,
        'user_query': user_query,
        'found_query': found_query,
        'lost_query': lost_query,
    }
    return render(request, 'dashboard/admin.html', context)


@admin_required
def admin_stats_api(request):
    return JsonResponse(_get_admin_stats())
