from django.urls import path
from .views import (
    TripCreateView, TripDetailView, TripListView, 
    trip_action, driver_location_update, driver_logout,
    DriverLocationListView
)
from .share_views import share_trip

urlpatterns = [
    path('', TripListView.as_view(), name='trips_list'),
    path('create/', TripCreateView.as_view(), name='trip_create'),
    path('<int:pk>/', TripDetailView.as_view(), name='trip_detail'),
    path('<int:pk>/action/', trip_action, name='trip_action'),
    path('location/', driver_location_update, name='driver_location_update'),
    path('locations/', DriverLocationListView.as_view(), name='driver_locations_list'),  # Admin list
    path('logout/', driver_logout, name='driver_logout'),
    path('share/<str:token>/', share_trip, name='share_trip'),
]
