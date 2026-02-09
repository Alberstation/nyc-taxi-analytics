"""
CSV and Parquet parsing for NYC TLC trip data.
Supports Yellow (tpep_*) and Green (lpep_*) schemas.
Datetime: epoch ms, epoch seconds, or ISO string.
"""
import io
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

TZ = ZoneInfo('America/New_York')

# Yellow taxi column mapping
YELLOW_COLS = {
    'tpep_pickup_datetime': 'pickup_datetime',
    'tpep_dropoff_datetime': 'dropoff_datetime',
    'PULocationID': 'pulocation_id',
    'DOLocationID': 'dolocation_id',
    'trip_distance': 'trip_distance',
    'fare_amount': 'fare_amount',
    'payment_type': 'payment_type',
    'passenger_count': 'passenger_count',
    'extra': 'extra',
    'mta_tax': 'mta_tax',
    'tip_amount': 'tip_amount',
    'tolls_amount': 'tolls_amount',
    'improvement_surcharge': 'improvement_surcharge',
    'total_amount': 'total_amount',
    'congestion_surcharge': 'congestion_surcharge',
    'Airport_fee': 'airport_fee',
    'cbd_congestion_fee': 'cbd_congestion_fee',
}

# Green taxi column mapping (lpep_* for pickup/dropoff)
GREEN_COLS = {
    'lpep_pickup_datetime': 'pickup_datetime',
    'lpep_dropoff_datetime': 'dropoff_datetime',
    'PULocationID': 'pulocation_id',
    'DOLocationID': 'dolocation_id',
    'trip_distance': 'trip_distance',
    'fare_amount': 'fare_amount',
    'payment_type': 'payment_type',
    'passenger_count': 'passenger_count',
    'extra': 'extra',
    'mta_tax': 'mta_tax',
    'tip_amount': 'tip_amount',
    'tolls_amount': 'tolls_amount',
    'improvement_surcharge': 'improvement_surcharge',
    'total_amount': 'total_amount',
    'congestion_surcharge': 'congestion_surcharge',
    'cbd_congestion_fee': 'cbd_congestion_fee',
}


def _parse_datetime(val):
    """Parse datetime from epoch ms, epoch seconds, or ISO string."""
    if val is None or (isinstance(val, float) and (val != val or val < 0)):
        return None
    if isinstance(val, datetime):
        return val.astimezone(TZ) if val.tzinfo else val.replace(tzinfo=TZ)
    try:
        x = float(val)
        if x > 1e12:  # epoch milliseconds
            return datetime.fromtimestamp(x / 1000, tz=TZ)
        return datetime.fromtimestamp(x, tz=TZ)
    except (ValueError, TypeError):
        pass
    try:
        return datetime.fromisoformat(str(val).replace('Z', '+00:00')).astimezone(TZ)
    except (ValueError, TypeError):
        return None


def _coerce_float(val, default=None):
    if val is None or (isinstance(val, float) and val != val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _coerce_int(val, default=None):
    if val is None or (isinstance(val, float) and val != val):
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def parse_parquet(path_or_file, cab_type, max_rows=100000):
    """
    Parse parquet file and yield dicts for TaxiTrip bulk_create.
    cab_type: 'yellow' or 'green'
    """
    df = pd.read_parquet(path_or_file)
    pickup_col = 'tpep_pickup_datetime' if cab_type == 'yellow' else 'lpep_pickup_datetime'
    dropoff_col = 'tpep_dropoff_datetime' if cab_type == 'yellow' else 'lpep_dropoff_datetime'

    if pickup_col not in df.columns:
        raise ValueError(f"Missing {pickup_col} - is this {cab_type} taxi data?")

    n = min(len(df), max_rows)
    for i in range(n):
        row = df.iloc[i]
        dt = _parse_datetime(row.get(pickup_col))
        if dt is None or dt.year != 2025:
            continue
        yield {
            'cab_type': cab_type,
            'pickup_datetime': dt,
            'dropoff_datetime': _parse_datetime(row.get(dropoff_col)) if dropoff_col in df.columns else None,
            'passenger_count': _coerce_float(row.get('passenger_count')),
            'trip_distance': _coerce_float(row.get('trip_distance')),
            'pulocation_id': _coerce_int(row.get('PULocationID')),
            'dolocation_id': _coerce_int(row.get('DOLocationID')),
            'payment_type': _coerce_float(row.get('payment_type')),
            'fare_amount': _coerce_float(row.get('fare_amount')),
            'extra': _coerce_float(row.get('extra')),
            'mta_tax': _coerce_float(row.get('mta_tax')),
            'tip_amount': _coerce_float(row.get('tip_amount')),
            'tolls_amount': _coerce_float(row.get('tolls_amount')),
            'improvement_surcharge': _coerce_float(row.get('improvement_surcharge')),
            'total_amount': _coerce_float(row.get('total_amount')),
            'congestion_surcharge': _coerce_float(row.get('congestion_surcharge')),
            'airport_fee': _coerce_float(row.get('Airport_fee')) if cab_type == 'yellow' else None,
            'cbd_congestion_fee': _coerce_float(row.get('cbd_congestion_fee')),
        }


def parse_csv(stream, cab_type, max_rows=100000):
    """
    Parse CSV and yield dicts for TaxiTrip bulk_create.
    Detects schema from headers (tpep_* vs lpep_*).
    """
    df = pd.read_csv(stream, nrows=max_rows)
    pickup_col = None
    dropoff_col = None
    for c in df.columns:
        if 'tpep_pickup' in c.lower() or (cab_type == 'yellow' and 'pickup' in c.lower()):
            pickup_col = c
        if 'tpep_dropoff' in c.lower() or 'lpep_dropoff' in c.lower() or 'dropoff' in c.lower():
            dropoff_col = c
    if pickup_col is None:
        for c in df.columns:
            if 'lpep_pickup' in c.lower() or (cab_type == 'green' and 'pickup' in c.lower()):
                pickup_col = c
                break
    if pickup_col is None:
        raise ValueError("Could not find pickup datetime column")

    for _, row in df.iterrows():
        dt = _parse_datetime(row.get(pickup_col))
        if dt is None or dt.year != 2025:
            continue
        puloc = row.get('PULocationID', row.get('pulocation_id'))
        doloc = row.get('DOLocationID', row.get('dolocation_id'))
        yield {
            'cab_type': cab_type,
            'pickup_datetime': dt,
            'dropoff_datetime': _parse_datetime(row.get(dropoff_col)) if dropoff_col else None,
            'passenger_count': _coerce_float(row.get('passenger_count')),
            'trip_distance': _coerce_float(row.get('trip_distance')),
            'pulocation_id': _coerce_int(puloc),
            'dolocation_id': _coerce_int(doloc),
            'payment_type': _coerce_float(row.get('payment_type')),
            'fare_amount': _coerce_float(row.get('fare_amount')),
            'extra': _coerce_float(row.get('extra')),
            'mta_tax': _coerce_float(row.get('mta_tax')),
            'tip_amount': _coerce_float(row.get('tip_amount')),
            'tolls_amount': _coerce_float(row.get('tolls_amount')),
            'improvement_surcharge': _coerce_float(row.get('improvement_surcharge')),
            'total_amount': _coerce_float(row.get('total_amount')),
            'congestion_surcharge': _coerce_float(row.get('congestion_surcharge')),
            'airport_fee': _coerce_float(row.get('Airport_fee')) if cab_type == 'yellow' else None,
            'cbd_congestion_fee': _coerce_float(row.get('cbd_congestion_fee')),
        }
