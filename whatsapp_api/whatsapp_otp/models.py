from django.db import models


class OTP(models.Model):
    phone_number = models.CharField(max_length=12)
    otp_code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
