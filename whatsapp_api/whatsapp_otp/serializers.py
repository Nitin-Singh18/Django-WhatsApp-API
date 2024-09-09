from rest_framework import serializers
from .models import OTP


class OTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['phone_number']
        read_only_fields = ['id', 'created_at', 'is_verified']


class OTPVerifySerial(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ['phone_number', "otp_code"]
