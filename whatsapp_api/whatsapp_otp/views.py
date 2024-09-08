import json

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import OTP
from .serializers import OTPSerializer, OTPVerifySerial
from django.utils import timezone
import random
import requests
from dotenv import load_dotenv
import os
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

load_dotenv()

headers = {
    "Authorization": os.getenv("WHATSAPP_API_TOKEN"),
    "Content-Type": "application/json"
}
url = os.getenv("WHATSAPP_API_URL")


# View to request OTP
@swagger_auto_schema(
    method='post',
    request_body=OTPSerializer,
    responses={
        200: openapi.Response('OTP sent successfully', OTPSerializer),
    })
@api_view(['POST'])
def request_otp(request):
    try:
        phone_number = request.data.get('phone_number')
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            otp_code = str(random.randint(1000, 9999))

            whatsapp_response = send_otp_via_whatsapp(phone_number=phone_number,
                                                      otp_code=otp_code)

            if whatsapp_response == status.HTTP_200_OK:
                OTP.objects.create(phone_number=phone_number, otp_code=otp_code)
                return Response(
                    {"message": "OTP sent successfully", "data": serializer.data, "otp": otp_code,
                     "whatsapp_res": whatsapp_response},
                    status=status.HTTP_200_OK)
            return Response({"whatsapp_code": whatsapp_response})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Function to send OTP via WhatsApp API
def send_otp_via_whatsapp(phone_number, otp_code):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "otp",
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": otp_code
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": otp_code
                        }
                    ]
                }
            ]
        }
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code


@swagger_auto_schema(
    method='post', request_body=OTPVerifySerial,
    responses={
        200: openapi.Response('OTP verified successfully'),
        400: openapi.Response('Invalid or expired OTP')
    })
@api_view(['POST'])
def verify_otp(request):
    serializer = OTPVerifySerial(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        otp_code = serializer.validated_data['otp_code']
        try:
            otp = OTP.objects.filter(phone_number=phone_number, otp_code=otp_code, is_verified=False).latest(
                'created_at')
        except OTP.DoesNotExist:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if (timezone.now() - otp.created_at).total_seconds() > 300:
            return Response({"error": "OTP has expired"}, status=status.HTTP_400_BAD_REQUEST)
        otp.verified = True
        otp.save()

        otp.delete()
        return Response({"success": "OTP verified successfully"}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# View to send promotional message
@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'phone_number': openapi.Schema(type=openapi.TYPE_STRING,
                                           description='Phone number'),
            'message_content': openapi.Schema(type=openapi.TYPE_STRING,
                                              description='Message'),
        }),
    responses={
        200: openapi.Response('Message sent successfully'),
        400: openapi.Response('Phone number and message content are required')
    })
@api_view(['POST'])
def send_promotional_message(request):
    phone_number = request.data.get('phone_number')
    message_content = request.data.get('message_content')

    if not phone_number or not message_content:
        return Response({"error": "Phone number and message are required."}, status=status.HTTP_400_BAD_REQUEST)

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "bytcra_promotion",
            "language": {
                "code": "en"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": message_content
                        }
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        if response.status_code == 200:
            return Response({"success": "Message sent successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": response_data}, status=response.status_code)

    except requests.RequestException as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
