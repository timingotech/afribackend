from rest_framework import serializers
from django.conf import settings
from .models import Trip, DriverLocation
from .models import Payment


class TripSerializer(serializers.ModelSerializer):
    # Extra read-only fields used by the admin/frontend
    customer_name = serializers.SerializerMethodField(read_only=True)
    rider_name = serializers.SerializerMethodField(read_only=True)
    estimated_fare = serializers.SerializerMethodField(read_only=True)
    final_fare = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ('id', 'customer', 'rider', 'status', 'created_at', 'accepted_at', 'started_at', 'ended_at')

    def get_customer_name(self, obj):
        try:
            return (obj.customer.get_full_name() or obj.customer.email)
        except Exception:
            return None

    def get_rider_name(self, obj):
        try:
            if not obj.rider:
                return None
            return (obj.rider.get_full_name() or obj.rider.email)
        except Exception:
            return None

    def _compute_price(self, obj_or_data):
        # Accept either a Trip instance or a dict-like with keys
        km = getattr(obj_or_data, 'distance_km', None) or obj_or_data.get('distance_km') if isinstance(obj_or_data, dict) else None
        mins = getattr(obj_or_data, 'duration_min', None) or obj_or_data.get('duration_min') if isinstance(obj_or_data, dict) else None
        try:
            km = float(km or 0)
        except Exception:
            km = 0.0
        try:
            mins = float(mins or 0)
        except Exception:
            mins = 0.0

        base = getattr(settings, 'TRIP_BASE_FARE', 2000.0)
        per_km = getattr(settings, 'TRIP_PER_KM', 500.0)
        per_min = getattr(settings, 'TRIP_PER_MIN', 50.0)
        surge = getattr(settings, 'TRIP_SURGE', 1.0)
        min_fare = getattr(settings, 'TRIP_MIN_FARE', 4000.0)

        calculated = (base + (per_km * km) + (per_min * mins)) * surge
        # enforce minimum fare
        final = max(min_fare, calculated)
        return round(final, 2)

    def get_estimated_fare(self, obj):
        if obj.price:
            return float(obj.price)
        try:
            return self._compute_price(obj)
        except Exception:
            return None

    def get_final_fare(self, obj):
        if obj.status == Trip.STATUS_COMPLETED and obj.price:
            return float(obj.price)
        return None

    def create(self, validated_data):
        # price calculation and minimum enforcement at creation time
        price = None
        try:
            price = self._compute_price(validated_data)
        except Exception:
            price = None
        if price is not None:
            validated_data['price'] = price
        # `customer` must be set by the view via serializer.save(customer=...)
        return super().create(validated_data)


class TripActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['accept', 'arrived', 'start', 'end', 'cancel'])
    rider_id = serializers.IntegerField(required=False)
    cancel_reason = serializers.CharField(required=False, allow_blank=True)


class DriverLocationSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    speed = serializers.FloatField(required=False)
    heading = serializers.FloatField(required=False)
    accuracy = serializers.FloatField(required=False)
    timestamp = serializers.DateTimeField(required=False)


class DriverLocationModelSerializer(serializers.ModelSerializer):
    driver = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DriverLocation
        fields = ['id', 'driver', 'lat', 'lng', 'speed', 'heading', 'accuracy', 'updated_at']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'trip', 'amount', 'provider', 'reference', 'status', 'metadata', 'raw_response', 'created_at', 'paid_at']
        read_only_fields = ['id', 'status', 'created_at', 'paid_at']
