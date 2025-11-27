from rest_framework import generics, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from apps.trips.models import Payment
from apps.trips.serializers import PaymentSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200


class AdminPaymentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        # restrict to admin/staff users
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return Payment.objects.select_related('trip__customer').all().order_by('-created_at')
        return Payment.objects.none()


class AdminPaymentDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
            return Payment.objects.select_related('trip__customer').all()
        return Payment.objects.none()



@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refund_payment(request, pk):
    user = request.user
    if not (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)):
        return Response({'detail': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

    payment = get_object_or_404(Payment, pk=pk)
    # Mark refunded locally; integration with provider refund API can be added later
    payment.mark_refunded(raw=str(request.data) or None)
    return Response(PaymentSerializer(payment).data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_payment_failed(request, pk):
    user = request.user
    if not (getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)):
        return Response({'detail': 'forbidden'}, status=status.HTTP_403_FORBIDDEN)

    payment = get_object_or_404(Payment, pk=pk)
    payment.mark_failed(raw=str(request.data) or None)
    return Response(PaymentSerializer(payment).data)
