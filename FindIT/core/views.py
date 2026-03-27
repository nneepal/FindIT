from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect, render

from .models import FoundItem, FoundItemClaim, LostItem
from .forms import FoundItemReportForm, LostItemSearchForm


def index(request):
    return render(request, 'core/index.html')


@login_required
def report_item(request):
    if request.method == 'POST':
        form = FoundItemReportForm(request.POST, request.FILES)
        if form.is_valid():
            found_item = form.save(commit=False)
            found_item.reported_by = request.user
            found_item.save()
            messages.success(request, 'Found item report submitted successfully.')
            return redirect('core:report')
        messages.error(request, 'Please fix the errors below and submit again.')
    else:
        form = FoundItemReportForm()

    return render(request, 'core/report.html', {'form': form})


@login_required
def search_item(request):
    if request.method == 'POST':
        form = LostItemSearchForm(request.POST, request.FILES)
        if form.is_valid():
            lost_item = form.save(commit=False)
            lost_item.searched_by = request.user
            lost_item.save()
            messages.success(request, 'Search request submitted and saved successfully.')
            return redirect('core:search')
        messages.error(request, 'Please fix the errors below and submit again.')
    else:
        form = LostItemSearchForm()

    return render(request, 'core/search.html', {'form': form})


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
    claimed_items = FoundItem.objects.filter(claim_status='claimed').prefetch_related(
        Prefetch(
            'claims',
            queryset=FoundItemClaim.objects.select_related('claimed_by').order_by('-created_at'),
        )
    ).order_by('-updated_at')

    context = {
        'claimed_items': claimed_items,
    }
    return render(request, 'core/pending_complaints.html', context)
