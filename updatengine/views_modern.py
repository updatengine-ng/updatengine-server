from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Max, Q
from django.utils import timezone
from datetime import timedelta

from inventory.models import machine, entity, software, net, osdistribution
from deploy.models import package, packagehistory, packageprofile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ONLINE_THRESHOLD_MINUTES = 60  # machine considered online if lastsave < 60 min ago


def _online_cutoff():
    return timezone.now() - timedelta(minutes=ONLINE_THRESHOLD_MINUTES)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    cutoff = _online_cutoff()
    total_machines = machine.objects.count()
    online_machines = machine.objects.filter(lastsave__gte=cutoff).count()
    offline_machines = total_machines - online_machines

    # Deployments in the last 24h
    since_24h = timezone.now() - timedelta(hours=24)
    recent_history = (
        packagehistory.objects
        .filter(date__gte=since_24h)
        .select_related('machine', 'package')
        .order_by('-date')[:10]
    )
    success_count = packagehistory.objects.filter(date__gte=since_24h, status='Operation completed').count()
    error_count = packagehistory.objects.filter(
        date__gte=since_24h, status__startswith='Error'
    ).count()
    inprogress_count = packagehistory.objects.filter(
        date__gte=since_24h, status='Install in progress'
    ).count()

    # Top entities by machine count
    top_entities = (
        entity.objects
        .annotate(machine_count=Count('machine'))
        .order_by('-machine_count')[:5]
    )

    # Machines without contact for more than 7 days
    stale_cutoff = timezone.now() - timedelta(days=7)
    stale_machines = machine.objects.filter(
        Q(lastsave__lt=stale_cutoff) | Q(lastsave__isnull=True)
    ).count()

    context = {
        'total_machines': total_machines,
        'online_machines': online_machines,
        'offline_machines': offline_machines,
        'online_pct': round(online_machines * 100 / total_machines, 1) if total_machines else 0,
        'recent_history': recent_history,
        'success_count': success_count,
        'error_count': error_count,
        'inprogress_count': inprogress_count,
        'stale_machines': stale_machines,
        'top_entities': top_entities,
        'total_packages': package.objects.count(),
    }
    return render(request, 'modern/dashboard.html', context)


# ---------------------------------------------------------------------------
# Dashboard — HTMX partial: live stats refresh
# ---------------------------------------------------------------------------

@login_required
def htmx_dashboard_stats(request):
    """Returns only the KPI cards fragment for HTMX polling."""
    cutoff = _online_cutoff()
    total_machines = machine.objects.count()
    online_machines = machine.objects.filter(lastsave__gte=cutoff).count()
    since_24h = timezone.now() - timedelta(hours=24)
    success_count = packagehistory.objects.filter(date__gte=since_24h, status='Operation completed').count()
    error_count = packagehistory.objects.filter(
        date__gte=since_24h, status__startswith='Error'
    ).count()
    context = {
        'total_machines': total_machines,
        'online_machines': online_machines,
        'online_pct': round(online_machines * 100 / total_machines, 1) if total_machines else 0,
        'success_count': success_count,
        'error_count': error_count,
    }
    return render(request, 'modern/partials/dashboard_stats.html', context)


# ---------------------------------------------------------------------------
# Inventory (Vue Parc)
# ---------------------------------------------------------------------------

@login_required
def inventory_view(request):
    cutoff = _online_cutoff()
    qs = machine.objects.select_related('entity', 'typemachine').prefetch_related(
        'osdistribution_set', 'net_set'
    ).order_by('name')

    # --- Filters ---
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    entity_filter = request.GET.get('entity', '')
    os_filter = request.GET.get('os', '')

    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(username__icontains=search) |
            Q(domain__icontains=search) |
            Q(net__ip__icontains=search)
        ).distinct()

    if status_filter == 'online':
        qs = qs.filter(lastsave__gte=cutoff)
    elif status_filter == 'offline':
        qs = qs.filter(Q(lastsave__lt=cutoff) | Q(lastsave__isnull=True))

    if entity_filter:
        qs = qs.filter(entity__id=entity_filter)

    if os_filter:
        qs = qs.filter(osdistribution__name__icontains=os_filter).distinct()

    # Annotate online status
    machines_list = []
    for m in qs:
        is_online = m.lastsave and m.lastsave >= cutoff
        os_obj = m.osdistribution_set.first()
        ip_obj = m.net_set.first()
        machines_list.append({
            'obj': m,
            'is_online': is_online,
            'os_name': os_obj.name if os_obj else 'N/A',
            'os_version': os_obj.version if os_obj else '',
            'ip': ip_obj.ip if ip_obj else 'N/A',
        })

    entities = entity.objects.order_by('name')

    # Distinct OS names for filter dropdown
    os_names = (
        osdistribution.objects
        .values_list('name', flat=True)
        .distinct()
        .order_by('name')
    )

    # HTMX partial: return only the table rows
    if request.headers.get('HX-Request'):
        return render(request, 'modern/partials/machines_rows.html', {
            'machines_list': machines_list,
            'cutoff': cutoff,
        })

    context = {
        'machines_list': machines_list,
        'entities': entities,
        'os_names': os_names,
        'total': qs.count(),
        'search': search,
        'status_filter': status_filter,
        'entity_filter': entity_filter,
        'os_filter': os_filter,
        'cutoff': cutoff,
    }
    return render(request, 'modern/inventory.html', context)


# ---------------------------------------------------------------------------
# Agent / Machine detail
# ---------------------------------------------------------------------------

@login_required
def machine_detail(request, machine_id):
    m = get_object_or_404(machine, pk=machine_id)
    cutoff = _online_cutoff()
    is_online = m.lastsave and m.lastsave >= cutoff

    os_list = osdistribution.objects.filter(host=m)
    net_list = net.objects.filter(host=m)
    software_list = software.objects.filter(host=m).order_by('name')
    history = (
        packagehistory.objects
        .filter(machine=m)
        .order_by('-date')[:20]
    )

    # Last seen delta
    last_seen = None
    if m.lastsave:
        delta = timezone.now() - m.lastsave
        if delta.seconds < 3600:
            last_seen = f'il y a {delta.seconds // 60} min'
        elif delta.days == 0:
            last_seen = f'il y a {delta.seconds // 3600}h'
        else:
            last_seen = f'il y a {delta.days} jour(s)'

    context = {
        'machine': m,
        'is_online': is_online,
        'os_list': os_list,
        'net_list': net_list,
        'software_list': software_list,
        'software_count': software_list.count(),
        'history': history,
        'last_seen': last_seen,
    }
    return render(request, 'modern/agent_detail.html', context)


# ---------------------------------------------------------------------------
# API JSON — machine search (for global search bar)
# ---------------------------------------------------------------------------

@login_required
def api_machine_search(request):
    q = request.GET.get('q', '').strip()
    results = []
    if len(q) >= 2:
        machines = machine.objects.filter(
            Q(name__icontains=q) | Q(username__icontains=q)
        )[:10]
        for m in machines:
            results.append({
                'id': m.id,
                'name': m.name,
                'username': m.username or '',
                'url': f'/inventory/{m.id}/',
            })
    return JsonResponse({'results': results})
