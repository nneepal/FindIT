from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import CharField, OuterRef, Prefetch, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.http import HttpResponseNotAllowed
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render

from .detection import detect_item_category
from .forms import ClaimVerificationForm, FoundItemReportForm, LostItemSearchForm
from .models import ClaimVerification, FoundItem, FoundItemClaim, LostItem, Notification


def index(request):
    return render(request, 'core/index.html')


@login_required
def report_item(request):
    detection_message = None
    detection_status_class = None

    if request.method == 'POST':
        post_data = request.POST.copy()
        uploaded_image = request.FILES.get('image')
        detection_result = None

        if uploaded_image and not post_data.get('category'):
            detection_result = detect_item_category(uploaded_image)
            post_data['category'] = detection_result['category_value']
            detection_message = detection_result['message']
            detection_status_class = 'is-error' if not detection_result['raw_label'] else 'is-detected'

        form = FoundItemReportForm(post_data, request.FILES)
        if form.is_valid():
            found_item = form.save(commit=False)
            found_item.reported_by = request.user
            found_item.save()
            if detection_result:
                messages.info(request, detection_result['message'])
            messages.success(request, 'Found item report submitted successfully.')
            return redirect('core:report')
        messages.error(request, 'Please fix the errors below and submit again.')
    else:
        form = FoundItemReportForm()

    return render(
        request,
        'core/report.html',
        {
            'form': form,
            'detection_message': detection_message,
            'detection_status_class': detection_status_class,
        },
    )


@login_required
def detect_report_category(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    uploaded_image = request.FILES.get('image')
    if not uploaded_image:
        return JsonResponse({'detail': 'No image uploaded.'}, status=400)

    detection_result = detect_item_category(uploaded_image)
    return JsonResponse(detection_result)


@login_required
def search_item(request):
    detection_message = None
    detection_status_class = None

    if request.method == 'POST':
        post_data = request.POST.copy()
        uploaded_image = request.FILES.get('image')
        detection_result = None

        if uploaded_image and not post_data.get('category'):
            detection_result = detect_item_category(uploaded_image)
            post_data['category'] = detection_result['category_value']
            detection_message = detection_result['message']
            detection_status_class = 'is-error' if not detection_result['raw_label'] else 'is-detected'

        form = LostItemSearchForm(post_data, request.FILES)
        if form.is_valid():
            lost_item = form.save(commit=False)
            lost_item.searched_by = request.user
            lost_item.save()
            if detection_result:
                messages.info(request, detection_result['message'])
            messages.success(request, 'Search request submitted and saved successfully.')
            return redirect('core:search')
        messages.error(request, 'Please fix the errors below and submit again.')
    else:
        form = LostItemSearchForm()

    return render(
        request,
        'core/search.html',
        {
            'form': form,
            'detection_message': detection_message,
            'detection_status_class': detection_status_class,
        },
    )


@login_required
def detect_search_category(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    uploaded_image = request.FILES.get('image')
    if not uploaded_image:
        return JsonResponse({'detail': 'No image uploaded.'}, status=400)

    detection_result = detect_item_category(uploaded_image)
    return JsonResponse(detection_result)


def listed_items(request):
    active_tab = request.GET.get('tab', 'found')
    if active_tab not in {'found', 'lost'}:
        active_tab = 'found'

    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', 'all').strip()
    sort = request.GET.get('sort', 'newest').strip()
    if sort not in {'newest', 'oldest'}:
        sort = 'newest'

    found_items = FoundItem.objects.select_related('reported_by')
    lost_items = LostItem.objects.select_related('searched_by')

    if query:
        found_items = found_items.filter(
            Q(item_name__icontains=query)
            | Q(description__icontains=query)
            | Q(location_found__icontains=query)
        )
        lost_items = lost_items.filter(
            Q(item_name__icontains=query)
            | Q(description__icontains=query)
            | Q(location_lost__icontains=query)
        )

    if category and category != 'all':
        found_items = found_items.filter(category=category)
        lost_items = lost_items.filter(category=category)

    if sort == 'oldest':
        found_items = found_items.order_by('date_found', 'created_at')
        lost_items = lost_items.order_by('date_lost', 'created_at')
    else:
        found_items = found_items.order_by('-date_found', '-created_at')
        lost_items = lost_items.order_by('-date_lost', '-created_at')

    claimed_item_ids = set()
    if request.user.is_authenticated:
        claimed_item_ids = set(
            FoundItemClaim.objects.filter(claimed_by=request.user).values_list('found_item_id', flat=True)
        )

    found_category_choices = dict(FoundItem.CATEGORY_CHOICES)
    lost_category_choices = dict(LostItem.CATEGORY_CHOICES)
    category_options = {}
    category_options.update(found_category_choices)
    category_options.update(lost_category_choices)

    context = {
        'active_tab': active_tab,
        'query': query,
        'category': category,
        'sort': sort,
        'found_items': found_items,
        'lost_items': lost_items,
        'category_options': sorted(category_options.items(), key=lambda x: x[1]),
        'claimed_item_ids': claimed_item_ids,
    }
    return render(request, 'core/listeditems.html', context)


@login_required
def claim_found_item(request, item_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    found_item = get_object_or_404(FoundItem, pk=item_id)
    claim, created = FoundItemClaim.objects.get_or_create(found_item=found_item, claimed_by=request.user)

    if created:
        found_item.claim_status = 'claimed'
        found_item.save(update_fields=['claim_status'])

        # Keep the claimant's matching lost reports in sync when a claim is created.
        LostItem.objects.filter(
            searched_by=request.user,
            item_name__iexact=found_item.item_name,
            category=found_item.category,
            claim_status='open',
        ).update(claim_status='claimed')
        messages.success(request, 'Item claim submitted and moved to pending complaints.')
    else:
        messages.info(request, 'You have already claimed this item.')

    return redirect('core:pending-complaints')


@login_required
def pending_complaints(request):
    verification_status_subquery = ClaimVerification.objects.filter(claim_id=OuterRef('pk')).values('status')[:1]

    claimed_items = FoundItem.objects.filter(
        claim_status='claimed',
    ).filter(
        Q(claims__verification__isnull=True) | ~Q(claims__verification__status='closed')
    ).distinct().prefetch_related(
        Prefetch(
            'claims',
            queryset=FoundItemClaim.objects.select_related('claimed_by').annotate(
                verification_status=Coalesce(
                    Subquery(verification_status_subquery),
                    Value('unverified'),
                    output_field=CharField(),
                )
            ).exclude(verification__status='closed').order_by('-created_at'),
        )
    ).order_by('-updated_at')

    user_claim_ids = set(
        FoundItemClaim.objects.filter(claimed_by=request.user).values_list('id', flat=True)
    )

    context = {
        'claimed_items': claimed_items,
        'user_claim_ids': user_claim_ids,
    }
    return render(request, 'core/pending_complaints.html', context)


@login_required
def verify_claim(request, claim_id):
    claim = get_object_or_404(
        FoundItemClaim.objects.select_related('found_item', 'claimed_by'),
        pk=claim_id,
        claimed_by=request.user,
    )

    verification_instance = getattr(claim, 'verification', None)

    if request.method == 'POST':
        form = ClaimVerificationForm(request.POST, request.FILES, instance=verification_instance)
        if form.is_valid():
            verification = form.save(commit=False)
            verification.claim = claim
            verification.found_item = claim.found_item
            verification.claimed_by = request.user
            verification.status = 'unverified'
            verification.admin_message = ''
            verification.reviewed_by = None
            verification.reviewed_at = None
            verification.save()

            admin_users = User.objects.filter(is_active=True).filter(
                Q(is_staff=True) | Q(is_superuser=True)
            ).distinct()
            if admin_users.exists():
                Notification.objects.bulk_create(
                    [
                        Notification(
                            recipient=admin_user,
                            title='New verification request',
                            message=(
                                f'{request.user.username} submitted verification details '
                                f'for "{claim.found_item.item_name}".'
                            ),
                            link=reverse('admin-dashboard'),
                        )
                        for admin_user in admin_users
                    ]
                )

            messages.success(request, 'Verification details submitted and sent to admin dashboard.')
            return redirect('core:pending-complaints')
        messages.error(request, 'Please fix the errors and submit the verification form again.')
    else:
        form = ClaimVerificationForm(instance=verification_instance)

    context = {
        'form': form,
        'claim': claim,
        'verification': verification_instance,
    }
    return render(request, 'core/claim_verification_form.html', context)


@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'core/notifications.html', {'notifications': notifications})
