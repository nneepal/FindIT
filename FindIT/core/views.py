from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

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
