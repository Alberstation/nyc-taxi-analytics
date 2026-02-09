"""
Django models for NYC Taxi Dashboard.
"""
from django.db import models


class TaxiZone(models.Model):
    """NYC TLC taxi zone with location for mapping."""
    location_id = models.IntegerField(unique=True, db_index=True)
    zone = models.CharField(max_length=100, blank=True)
    borough = models.CharField(max_length=50, blank=True)
    lat = models.FloatField(default=40.73)
    lon = models.FloatField(default=-73.99)

    class Meta:
        ordering = ['location_id']

    def __str__(self):
        return f"{self.zone or self.location_id} ({self.location_id})"


class TaxiTrip(models.Model):
    """Single taxi trip record (Yellow or Green)."""
    cab_type = models.CharField(max_length=10, db_index=True)  # 'yellow' or 'green'
    pickup_datetime = models.DateTimeField(db_index=True)
    dropoff_datetime = models.DateTimeField(null=True, blank=True)
    passenger_count = models.FloatField(null=True, blank=True)
    trip_distance = models.FloatField(null=True, blank=True)
    pulocation_id = models.IntegerField(null=True, blank=True, db_index=True)
    dolocation_id = models.IntegerField(null=True, blank=True)
    payment_type = models.FloatField(null=True, blank=True)
    fare_amount = models.FloatField(null=True, blank=True)
    extra = models.FloatField(null=True, blank=True)
    mta_tax = models.FloatField(null=True, blank=True)
    tip_amount = models.FloatField(null=True, blank=True)
    tolls_amount = models.FloatField(null=True, blank=True)
    improvement_surcharge = models.FloatField(null=True, blank=True)
    total_amount = models.FloatField(null=True, blank=True)
    congestion_surcharge = models.FloatField(null=True, blank=True)
    airport_fee = models.FloatField(null=True, blank=True)
    cbd_congestion_fee = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ['-pickup_datetime']
        indexes = [
            models.Index(fields=['cab_type', 'pickup_datetime']),
            models.Index(fields=['cab_type', 'pulocation_id']),
        ]
