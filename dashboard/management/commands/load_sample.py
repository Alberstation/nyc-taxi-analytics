"""
Pre-load sample parquet files from data/ directory.
 green_tripdata_2025-01,02,03.parquet
 yellow_tripdata_2025-01,02,03.parquet
Deletes any trips from years other than 2025 before loading.
"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db.models import Q

from dashboard.models import TaxiTrip
from dashboard.parsers import parse_parquet

TZ = ZoneInfo('America/New_York')
YEAR_2025_START = datetime(2025, 1, 1, tzinfo=TZ)
YEAR_2025_END = datetime(2026, 1, 1, tzinfo=TZ)

SAMPLE_FILES = [
    ('yellow', 'yellow_tripdata_2025-01.parquet'),
    ('yellow', 'yellow_tripdata_2025-02.parquet'),
    ('yellow', 'yellow_tripdata_2025-03.parquet'),
    ('green', 'green_tripdata_2025-01.parquet'),
    ('green', 'green_tripdata_2025-02.parquet'),
    ('green', 'green_tripdata_2025-03.parquet'),
]


class Command(BaseCommand):
    help = 'Pre-load sample yellow and green taxi parquet files from data/'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-rows',
            type=int,
            default=50000,
            help='Max rows per file (default: 50000)',
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            default=None,
            help='Override data directory path',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip loading if 2025 data already exists',
        )

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        data_dir = Path(options['data_dir']) if options['data_dir'] else base_dir / 'data'
        max_rows = options['max_rows']

        if options.get('skip_existing') and TaxiTrip.objects.filter(
            pickup_datetime__gte=YEAR_2025_START,
            pickup_datetime__lt=YEAR_2025_END,
        ).exists():
            self.stdout.write('2025 data already loaded, skipping')
            return

        # Delete any data from years other than 2025
        deleted, _ = TaxiTrip.objects.filter(
            Q(pickup_datetime__lt=YEAR_2025_START) | Q(pickup_datetime__gte=YEAR_2025_END)
        ).delete()
        if deleted:
            self.stdout.write(f'Deleted {deleted} trips from previous/future years')

        total = 0
        for cab_type, fname in SAMPLE_FILES:
            path = data_dir / fname
            if not path.exists():
                self.stdout.write(self.style.WARNING(f'Skip {fname} (not found)'))
                continue
            try:
                rows = list(parse_parquet(path, cab_type, max_rows=max_rows))
                objs = [TaxiTrip(**r) for r in rows]
                TaxiTrip.objects.bulk_create(objs)
                total += len(objs)
                self.stdout.write(f'Loaded {len(objs)} {cab_type} trips from {fname}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed {fname}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'Pre-loaded {total} trips total'))
