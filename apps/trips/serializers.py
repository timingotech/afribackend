from rest_framework import serializers
from .models import Trip


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ('id', 'customer', 'rider', 'status', 'created_at', 'accepted_at', 'started_at', 'ended_at')


class TripActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['accept', 'arrived', 'start', 'end', 'cancel'])
    rider_id = serializers.IntegerField(required=False)
    cancel_reason = serializers.CharField(required=False, allow_blank=True)
