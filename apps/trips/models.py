from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Trip(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_ARRIVED = 'arrived'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELED = 'canceled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_ARRIVED, 'Arrived'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELED, 'Canceled'),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='customer_trips', on_delete=models.CASCADE)
    rider = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='rider_trips', on_delete=models.SET_NULL, null=True, blank=True)

    origin_address = models.CharField(max_length=255)
    origin_lat = models.FloatField(null=True, blank=True)
    origin_lng = models.FloatField(null=True, blank=True)

    dest_address = models.CharField(max_length=255)
    dest_lat = models.FloatField(null=True, blank=True)
    dest_lng = models.FloatField(null=True, blank=True)

    distance_km = models.FloatField(null=True, blank=True)
    duration_min = models.FloatField(null=True, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    canceled_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='cancellations', on_delete=models.SET_NULL, null=True, blank=True)
    # Shareable tracking token and live flag
    share_token = models.CharField(max_length=64, null=True, blank=True, unique=True)
    live_active = models.BooleanField(default=False)

    def calculate_price(self, base=2.0, per_km=1.0, per_min=0.2, surge=1.0):
        km = self.distance_km or 0
        mins = self.duration_min or 0
        self.price = (base + (per_km * km) + (per_min * mins)) * surge
        return self.price

    def accept(self, rider):
        self.rider = rider
        self.status = self.STATUS_ACCEPTED
        self.accepted_at = timezone.now()
        self.save()

    def arrived(self):
        self.status = self.STATUS_ARRIVED
        self.arrived_at = timezone.now()
        self.save()

    def start(self):
        self.status = self.STATUS_IN_PROGRESS
        self.started_at = timezone.now()
        # generate a share token for live tracking viewers
        if not self.share_token:
            self.share_token = uuid.uuid4().hex
        self.live_active = True
        self.save()
        # Persist share token in Redis with TTL if Redis is configured
        try:
            from django.conf import settings
            redis_url = getattr(settings, 'REDIS_URL', None)
            if redis_url and self.share_token:
                import redis
                key = f"{getattr(settings, 'SHARE_TOKEN_REDIS_PREFIX', 'share:token:')}{self.share_token}"
                r = redis.from_url(redis_url)
                # store trip id for reverse lookup and set TTL
                ttl = getattr(settings, 'SHARE_TOKEN_TTL_SECONDS', 6 * 3600)
                r.setex(key, ttl, str(self.pk))
        except Exception:
            pass

    def end(self):
        self.status = self.STATUS_COMPLETED
        self.ended_at = timezone.now()
        # revoke share token in Redis and clear live flag
        try:
            from django.conf import settings
            redis_url = getattr(settings, 'REDIS_URL', None)
            if redis_url and self.share_token:
                import redis
                key = f"{getattr(settings, 'SHARE_TOKEN_REDIS_PREFIX', 'share:token:')}{self.share_token}"
                r = redis.from_url(redis_url)
                try:
                    r.delete(key)
                except Exception:
                    pass
        except Exception:
            pass
        self.live_active = False
        self.share_token = None
        self.save()

    def cancel(self, by_user=None):
        self.status = self.STATUS_CANCELED
        self.canceled_at = timezone.now()
        self.canceled_by = by_user
        # revoke share token when canceled
        try:
            from django.conf import settings
            redis_url = getattr(settings, 'REDIS_URL', None)
            if redis_url and self.share_token:
                import redis
                key = f"{getattr(settings, 'SHARE_TOKEN_REDIS_PREFIX', 'share:token:')}{self.share_token}"
                r = redis.from_url(redis_url)
                try:
                    r.delete(key)
                except Exception:
                    pass
        except Exception:
            pass
        self.live_active = False
        self.share_token = None
        self.save()

    def __str__(self):
        return f'Trip({self.pk}) {self.status}'


class DriverLocation(models.Model):
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='locations', on_delete=models.CASCADE)
    lat = models.FloatField()
    lng = models.FloatField()
    speed = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    accuracy = models.FloatField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['lat', 'lng']),
        ]

    def __str__(self):
        return f'DriverLocation({self.driver}, {self.lat},{self.lng})'


class Payment(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_SUCCESS = 'success'
    STATUS_FAILED = 'failed'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SUCCESS, 'Success'),
        (STATUS_FAILED, 'Failed'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    trip = models.ForeignKey(Trip, related_name='payments', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    provider = models.CharField(max_length=64, default='paystack')
    reference = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    metadata = models.JSONField(null=True, blank=True)
    raw_response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def mark_paid(self, raw=None):
        self.status = self.STATUS_SUCCESS
        self.paid_at = timezone.now()
        if raw:
            self.raw_response = raw
        self.save()

    def mark_failed(self, raw=None):
        self.status = self.STATUS_FAILED
        if raw:
            self.raw_response = raw
        self.save()

    def mark_refunded(self, raw=None):
        self.status = self.STATUS_REFUNDED
        if raw:
            self.raw_response = raw
        self.save()

    def __str__(self):
        return f'Payment({self.reference}, {self.amount}, {self.status})'
