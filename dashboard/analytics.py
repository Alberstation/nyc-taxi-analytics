"""
Analytics queries and ML models for NYC Taxi Dashboard.
All data is restricted to 2025.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.db.models import Count, Avg
from django.db.models.functions import TruncDate, ExtractHour, ExtractWeekDay
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.linear_model import Ridge
from sklearn.cluster import DBSCAN
import numpy as np

from .models import TaxiTrip, TaxiZone

TZ = ZoneInfo('America/New_York')
YEAR_2025_START = datetime(2025, 1, 1, tzinfo=TZ)
YEAR_2025_END = datetime(2026, 1, 1, tzinfo=TZ)

# Payment type labels (TLC numeric codes)
PAYMENT_LABELS = {
    0: 'Flex Fare trip',
    1: 'Credit card',
    2: 'Cash',
    3: 'No charge',
    4: 'Dispute',
    5: 'Unknown',
    6: 'Voided trip',
}
WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _base_qs(cab_type):
    """Base queryset: cab type filter + 2025 only."""
    qs = TaxiTrip.objects.filter(
        pickup_datetime__gte=YEAR_2025_START,
        pickup_datetime__lt=YEAR_2025_END,
    )
    if cab_type and cab_type != 'all':
        qs = qs.filter(cab_type=cab_type)
    return qs


def get_metrics(cab_type):
    qs = _base_qs(cab_type)
    total = qs.count()
    if total == 0:
        return {'total_trips': 0, 'avg_fare': 0, 'avg_distance': 0, 'busiest_hour': 'N/A'}
    avg_fare = round(qs.aggregate(Avg('fare_amount'))['fare_amount__avg'] or 0, 2)
    avg_dist = round(qs.aggregate(Avg('trip_distance'))['trip_distance__avg'] or 0, 2)
    by_hour = qs.annotate(h=ExtractHour('pickup_datetime')).values('h').annotate(c=Count('id')).order_by('-c')
    busiest = by_hour.first()
    busiest_hour = f"{busiest['h']:02d}:00" if busiest else 'N/A'
    return {'total_trips': total, 'avg_fare': avg_fare, 'avg_distance': avg_dist, 'busiest_hour': busiest_hour}


def get_trips_over_time(cab_type):
    qs = _base_qs(cab_type).annotate(d=TruncDate('pickup_datetime')).values('d').annotate(c=Count('id')).order_by('d')
    labels = []
    data = []
    for r in qs:
        d_val = r['d']
        if hasattr(d_val, 'strftime'):
            labels.append(d_val.strftime('%Y-%m-%d'))
        else:
            labels.append(str(d_val)[:10])  # e.g. "2025-01-15"
        data.append(int(r['c']))
    return {'labels': labels, 'data': data}


def get_trips_by_hour(cab_type):
    qs = _base_qs(cab_type).annotate(h=ExtractHour('pickup_datetime')).values('h').annotate(c=Count('id')).order_by('h')
    by_h = {r['h']: r['c'] for r in qs}
    labels = [f"{i:02d}:00" for i in range(24)]
    data = [by_h.get(i, 0) for i in range(24)]
    return {'labels': labels, 'data': data}


def get_trips_by_weekday(cab_type):
    qs = _base_qs(cab_type).annotate(wd=ExtractWeekDay('pickup_datetime')).values('wd').annotate(c=Count('id')).order_by('wd')
    by_wd = {r['wd']: r['c'] for r in qs}  # 1=Sun, 2=Mon, ..., 7=Sat in Django
    labels = WEEKDAY_LABELS  # Mon..Sun
    wd_order = [2, 3, 4, 5, 6, 7, 1]  # Mon=2, Tue=3, ..., Sun=1
    data = [by_wd.get(wd_order[i], 0) for i in range(7)]
    return {'labels': labels, 'data': data}


def get_payment_type(cab_type):
    qs = _base_qs(cab_type).values('payment_type').annotate(c=Count('id')).order_by('-c')
    labels = [PAYMENT_LABELS.get(int(r['payment_type'] or 0), f"Type {r['payment_type']}") for r in qs]
    data = [r['c'] for r in qs]
    return {'labels': labels, 'data': data}


def get_heatmap(cab_type, top_n=80):
    qs = _base_qs(cab_type).values('pulocation_id').annotate(c=Count('id')).order_by('-c')[:top_n]
    zone_ids = [r['pulocation_id'] for r in qs]
    zone_map = {z.location_id: z for z in TaxiZone.objects.filter(location_id__in=zone_ids)}
    points = []
    for r in qs:
        z = zone_map.get(r['pulocation_id'])
        if z:
            points.append({'zone': z.zone or str(r['pulocation_id']), 'lat': z.lat, 'lon': z.lon, 'count': r['c']})
    return {'points': points}


def get_demand_predictions(cab_type):
    """Ridge + Polynomial (degree=2), forecast next 7 days."""
    qs = _base_qs(cab_type).annotate(d=TruncDate('pickup_datetime')).values('d').annotate(c=Count('id')).order_by('d')
    daily = list(qs)
    if len(daily) < 7:
        return {'labels': [], 'actual': [], 'predicted': []}
    last_31 = daily[-31:]
    X = []
    y = []
    for r in last_31:
        d = r['d']
        X.append([d.weekday(), d.day, d.month])
        y.append(r['c'])
    X = np.array(X)
    y = np.array(y)
    pipe = Pipeline([
        ('poly', PolynomialFeatures(degree=2, include_bias=False)),
        ('scaler', StandardScaler()),
        ('ridge', Ridge(alpha=1.0, random_state=42)),
    ])
    pipe.fit(X, y)
    last_14_days = daily[-14:]
    labels = [r['d'].strftime('%Y-%m-%d') for r in last_14_days]
    actual = [r['c'] for r in last_14_days]
    pred = list(actual)
    last_d = last_14_days[-1]['d']
    for i in range(7):
        next_d = last_d + timedelta(days=i + 1)
        x_pred = np.array([[next_d.weekday(), next_d.day, next_d.month]])
        pred.append(float(pipe.predict(x_pred)[0]))
        labels.append(next_d.strftime('%Y-%m-%d'))
    return {'labels': labels, 'actual': actual + [None] * 7, 'predicted': pred}


def get_duration_predictions(cab_type, top_n=20):
    """Fare distribution: top N trips by distance, actual fare."""
    qs = _base_qs(cab_type).filter(
        trip_distance__gt=0,
        fare_amount__gte=0,
        fare_amount__lt=500
    ).order_by('pickup_datetime').values('trip_distance', 'fare_amount')[:1500]
    trips = list(qs)
    if len(trips) < 50:
        return {'labels': [], 'actual': []}
    # Sort by distance and take top N
    sorted_trips = sorted(trips, key=lambda t: t['trip_distance'], reverse=True)[:top_n]
    labels = [f"{t['trip_distance']:.1f}" for t in sorted_trips]
    actual = [round(t['fare_amount'], 2) for t in sorted_trips]
    return {'labels': labels, 'actual': actual}


def get_cluster_zones(cab_type, eps=0.01, min_samples=4, top_zones=150):
    """DBSCAN clustering of top zones by pickup count."""
    qs = _base_qs(cab_type).values('pulocation_id').annotate(c=Count('id')).order_by('-c')[:top_zones]
    zone_ids = [r['pulocation_id'] for r in qs]
    zones = list(TaxiZone.objects.filter(location_id__in=zone_ids))
    if len(zones) < min_samples:
        return {'zones': []}
    coords = np.array([[z.lat, z.lon] for z in zones])
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='euclidean').fit(coords)
    labels = clustering.labels_
    count_map = {r['pulocation_id']: r['c'] for r in qs}
    result = []
    for z, lab in zip(zones, labels):
        result.append({
            'zone': z.zone or str(z.location_id),
            'lat': z.lat,
            'lon': z.lon,
            'count': count_map.get(z.location_id, 0),
            'cluster': int(lab),
        })
    return {'zones': result}
