"""
Load NYC taxi zones from TLC lookup table.
Fetches from https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
or uses borough centroids as fallback.
"""
import csv
import urllib.request
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from dashboard.models import TaxiZone

# Borough approximate centroids (lat, lon) when zone lookup has no coords
BOROUGH_CENTROIDS = {
    'Manhattan': (40.7589, -73.9851),
    'Brooklyn': (40.6501, -73.9495),
    'Queens': (40.7282, -73.7949),
    'Bronx': (40.8448, -73.8648),
    'Staten Island': (40.5795, -74.1502),
    'EWR': (40.6895, -74.1745),
    'Unknown': (40.73, -73.99),
}

ZONE_LOOKUP_URL = 'https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv'


def load_from_url():
    """Fetch and parse zone lookup from TLC."""
    with urllib.request.urlopen(ZONE_LOOKUP_URL, timeout=10) as f:
        reader = csv.DictReader(f.read().decode('utf-8').splitlines())
        rows = list(reader)
    return rows


def load_from_local(base_dir):
    """Load from local data file if present."""
    for name in ('taxi_zone_lookup.csv', 'zones.csv'):
        path = base_dir / name
        if path.exists():
            with open(path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
    return None


class Command(BaseCommand):
    help = 'Load NYC taxi zones from TLC lookup table'

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        rows = load_from_local(base_dir)
        if not rows:
            try:
                rows = load_from_url()
                self.stdout.write('Fetched zone lookup from TLC')
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not fetch zones: {e}'))
                self._create_placeholder_zones()
                return

        with transaction.atomic():
            TaxiZone.objects.all().delete()
            created = 0
            for row in rows:
                lid = row.get('LocationID') or row.get('location_id') or row.get('LocationId')
                if not lid:
                    continue
                try:
                    lid = int(lid)
                except (ValueError, TypeError):
                    continue
                zone = row.get('Zone') or row.get('zone') or ''
                borough = row.get('Borough') or row.get('borough') or 'Unknown'
                lat, lon = BOROUGH_CENTROIDS.get(borough, BOROUGH_CENTROIDS['Unknown'])
                TaxiZone.objects.create(
                    location_id=lid,
                    zone=zone[:100] if zone else '',
                    borough=borough[:50] if borough else '',
                    lat=lat,
                    lon=lon,
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} taxi zones'))

    def _create_placeholder_zones(self):
        """Create minimal zones 1-263 with NYC center when no lookup available."""
        with transaction.atomic():
            TaxiZone.objects.all().delete()
            for i in range(1, 264):
                TaxiZone.objects.create(
                    location_id=i,
                    zone=f'Zone {i}',
                    borough='',
                    lat=40.73,
                    lon=-73.99,
                )
        self.stdout.write(self.style.WARNING('Created 263 placeholder zones (no lookup available)'))
