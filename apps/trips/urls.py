from django.urls import path
from .views import (
    TripCreateView, TripDetailView, TripListView, 
    trip_action, driver_location_update, driver_logout,
    DriverLocationListView, estimate_fare, create_payment, paystack_webhook
)
from .views import reassign_trip
from .share_views import share_trip

urlpatterns = [
    path('', TripListView.as_view(), name='trips_list'),
    path('create/', TripCreateView.as_view(), name='trip_create'),
    path('<int:pk>/', TripDetailView.as_view(), name='trip_detail'),
    path('<int:pk>/action/', trip_action, name='trip_action'),
    path('<int:pk>/reassign/', reassign_trip, name='trip_reassign'),
    path('estimate/', estimate_fare, name='trip_estimate'),
    path('estimate/route/', estimate_fare, name='trip_estimate_route'),
    path('<int:pk>/pay/', create_payment, name='trip_create_payment'),
    path('payments/paystack/webhook/', paystack_webhook, name='paystack_webhook'),
    path('location/', driver_location_update, name='driver_location_update'),
    path('locations/', DriverLocationListView.as_view(), name='driver_locations_list'),  # Admin list
    path('logout/', driver_logout, name='driver_logout'),
    path('share/<str:token>/', share_trip, name='share_trip'),
]
