from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from .models import Trip
from .serializers import TripSerializer, TripActionSerializer


class TripCreateView(generics.CreateAPIView):
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class TripDetailView(generics.RetrieveAPIView):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]


class TripListView(generics.ListAPIView):
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'customer':
            return Trip.objects.filter(customer=user).order_by('-created_at')
        if user.role == 'rider':
            return Trip.objects.filter(rider=user).order_by('-created_at')
        return Trip.objects.none()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trip_action(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    serializer = TripActionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    action = serializer.validated_data['action']

    if action == 'accept':
        if request.user.role != 'rider':
            return Response({'detail': 'Only riders can accept trips'}, status=status.HTTP_403_FORBIDDEN)
        trip.accept(request.user)
        return Response(TripSerializer(trip).data)

    if action == 'start':
        if request.user.role != 'rider':
            return Response({'detail': 'Only riders can start trips'}, status=status.HTTP_403_FORBIDDEN)
        trip.start()
        return Response(TripSerializer(trip).data)

    if action == 'end':
        if request.user.role != 'rider':
            return Response({'detail': 'Only riders can end trips'}, status=status.HTTP_403_FORBIDDEN)
        trip.end()
        return Response(TripSerializer(trip).data)

    if action == 'cancel':
        trip.cancel(by_user=request.user)
        return Response(TripSerializer(trip).data)

    return Response({'detail': 'action not handled'}, status=status.HTTP_400_BAD_REQUEST)
