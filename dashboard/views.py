"""
API views for NYC Taxi Dashboard.
"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from . import analytics
from .models import TaxiTrip
from .parsers import parse_parquet, parse_csv


def _cab_type(request):
    return request.GET.get('cab_type', 'all') or 'all'


@require_http_methods(["GET"])
def metrics(request):
    return JsonResponse(analytics.get_metrics(_cab_type(request)))


@require_http_methods(["GET"])
def trips_over_time(request):
    return JsonResponse(analytics.get_trips_over_time(_cab_type(request)))


@require_http_methods(["GET"])
def trips_by_hour(request):
    return JsonResponse(analytics.get_trips_by_hour(_cab_type(request)))


@require_http_methods(["GET"])
def trips_by_weekday(request):
    return JsonResponse(analytics.get_trips_by_weekday(_cab_type(request)))


@require_http_methods(["GET"])
def payment_type(request):
    return JsonResponse(analytics.get_payment_type(_cab_type(request)))


@require_http_methods(["GET"])
def heatmap(request):
    return JsonResponse(analytics.get_heatmap(_cab_type(request)))


@require_http_methods(["GET"])
def demand_predictions(request):
    return JsonResponse(analytics.get_demand_predictions(_cab_type(request)))


@require_http_methods(["GET"])
def cluster_zones(request):
    return JsonResponse(analytics.get_cluster_zones(_cab_type(request)))


@require_http_methods(["GET"])
def duration_predictions(request):
    return JsonResponse(analytics.get_duration_predictions(_cab_type(request)))


@require_http_methods(["GET"])
def dashboard_all(request):
    """Single request returning all dashboard data."""
    cab = _cab_type(request)
    return JsonResponse({
        'metrics': analytics.get_metrics(cab),
        'trips_over_time': analytics.get_trips_over_time(cab),
        'trips_by_hour': analytics.get_trips_by_hour(cab),
        'trips_by_weekday': analytics.get_trips_by_weekday(cab),
        'payment_type': analytics.get_payment_type(cab),
        'heatmap': analytics.get_heatmap(cab),
        'demand_predictions': analytics.get_demand_predictions(cab),
        'cluster_zones': analytics.get_cluster_zones(cab),
        'duration_predictions': analytics.get_duration_predictions(cab),
    })


@require_http_methods(["POST"])
@csrf_exempt
def upload(request):
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
    file = request.FILES['file']
    cab_type = request.POST.get('cab_type', 'yellow')
    if cab_type not in ('yellow', 'green'):
        return JsonResponse({'error': 'cab_type must be yellow or green'}, status=400)
    max_rows = int(request.POST.get('max_rows', 100000))

    try:
        ext = (file.name or '').lower()
        if ext.endswith('.parquet'):
            rows = list(parse_parquet(file, cab_type, max_rows))
        else:
            rows = list(parse_csv(file, cab_type, max_rows))

        objs = [TaxiTrip(**r) for r in rows]
        TaxiTrip.objects.bulk_create(objs)
        return JsonResponse({'uploaded': len(objs), 'cab_type': cab_type})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@require_http_methods(["POST"])
@csrf_exempt
def load_sample(request):
    """Load sample parquet files from data/ directory. Deletes non-2025 data first."""
    TZ = ZoneInfo('America/New_York')
    year_start = datetime(2025, 1, 1, tzinfo=TZ)
    year_end = datetime(2026, 1, 1, tzinfo=TZ)
    TaxiTrip.objects.filter(
        Q(pickup_datetime__lt=year_start) | Q(pickup_datetime__gte=year_end)
    ).delete()

    data_dir = Path(__file__).resolve().parent.parent / 'data'
    patterns = [
        ('yellow', 'yellow_tripdata_2025-01.parquet'),
        ('yellow', 'yellow_tripdata_2025-02.parquet'),
        ('yellow', 'yellow_tripdata_2025-03.parquet'),
        ('green', 'green_tripdata_2025-01.parquet'),
        ('green', 'green_tripdata_2025-02.parquet'),
        ('green', 'green_tripdata_2025-03.parquet'),
    ]
    total = 0
    for cab, fname in patterns:
        path = data_dir / fname
        if not path.exists():
            continue
        try:
            rows = list(parse_parquet(path, cab, max_rows=50000))
            objs = [TaxiTrip(**r) for r in rows]
            TaxiTrip.objects.bulk_create(objs)
            total += len(objs)
        except Exception:
            pass
    return JsonResponse({'loaded': total})
