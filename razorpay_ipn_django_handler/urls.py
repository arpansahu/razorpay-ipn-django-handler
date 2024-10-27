from django.urls import path
from .views import razorpay_ipn_receiver_view

urlpatterns = [
    path('webhook/', razorpay_ipn_receiver_view, name='razorpay_ipn_receiver_view'),
]
