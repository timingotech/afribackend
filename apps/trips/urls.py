from django.urls import path
from .views import TripCreateView, TripDetailView, TripListView, trip_action

urlpatterns = [
    path('', TripListView.as_view(), name='trips_list'),
    path('create/', TripCreateView.as_view(), name='trip_create'),
    path('<int:pk>/', TripDetailView.as_view(), name='trip_detail'),
    path('<int:pk>/action/', trip_action, name='trip_action'),
]
