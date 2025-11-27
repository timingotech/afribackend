from django.urls import path
from . import views
from .views import AdminPaymentListView, AdminPaymentDetailView

urlpatterns = [
    path('', AdminPaymentListView.as_view(), name='payments_list'),
    path('<int:pk>/', AdminPaymentDetailView.as_view(), name='payments_detail'),
    path('<int:pk>/refund/', views.refund_payment, name='admin-payment-refund'),
    path('<int:pk>/mark_failed/', views.mark_payment_failed, name='admin-payment-mark-failed'),
]
