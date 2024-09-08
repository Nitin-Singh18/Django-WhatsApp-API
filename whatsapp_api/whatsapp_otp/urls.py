from django.urls import path
from .views import request_otp, verify_otp, send_promotional_message

urlpatterns = [
    path('request-otp', request_otp, name='request_otp'),
    path('verify-otp', verify_otp, name='verify_otp'),
    path('send-promotional-message', send_promotional_message, name='send_promotional_message'),
]
