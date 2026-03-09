from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.db import models
from .serializers import (
    RegisterSerializer, LoginSerializer,DepositSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,UserProfileSerializer
)
from django.contrib.auth import get_user_model
from .models import EmailOTP,WalletTransaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import uuid
import requests
from django.conf import settings
from SoftwareManagements.models import Software
# from django.http import FileResponse
import os

User = get_user_model()

class AuthViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"msg": "User registered successfully"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def login(self, request):
        identifier = request.data.get("email")
        password = request.data.get("password")

        if not identifier or not password:
            return Response(
                {"error": "Email or Phone number and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🔎 Find user by email OR username OR phone
        user = User.objects.filter(
            models.Q(email__iexact=identifier) |
            models.Q(username__iexact=identifier) |
            models.Q(phone_number__iexact=identifier)
        ).first()

        if not user:
            return Response(
                {"error": "No active user found with this username"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # 🔐 Authenticate using username (Django expects username)
        user = authenticate(username=user.username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            serializer=UserProfileSerializer(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "profile":serializer.data
            })

        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    @action(detail=False, methods=['post'])
    def request_password_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        if not User.objects.filter(email=email).exists():
            return Response({"error": "User with this email does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        otp = EmailOTP.generate_otp()
        EmailOTP.objects.create(email=email, otp=otp)
        # send OTP via email
        send_mail(
            'Password Reset OTP',
            f'Your OTP code is {otp}. It is valid for 10 minutes.',
            settings.EMAIL_HOST_USER,
            [email],
        )
        return Response({"msg": "OTP sent to your email"})

    @action(detail=False, methods=['post'])
    def confirm_password_reset(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        try:
            otp_record = EmailOTP.objects.filter(email=email, otp=otp, verified=False).latest('created_at')
        except EmailOTP.DoesNotExist:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        if not otp_record.is_valid():
            return Response({"error": "OTP expired or already used"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        otp_record.verified = True
        otp_record.save()

        return Response({"msg": "Password reset successful"})
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current logged-in user profile with balance"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['patch'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update current logged-in user profile (username, phone)"""
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
# Wallet View Set
class WalletViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # -----------------------------
    # MANUAL DEPOSIT
    # -----------------------------
    @action(detail=False, methods=["post"])
    def manual_deposit(self, request):

        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaction = WalletTransaction.objects.create(
            user=request.user,
            amount=serializer.validated_data["amount"],
            type="manual",
            proof=serializer.validated_data.get("proof"),
            status="pending",
            reference=str(uuid.uuid4())
        )

        return Response({
            "message": "Deposit submitted. Waiting for approval.",
            "reference": transaction.reference
        })



    @action(detail=False, methods=["post"])
    def crypto_deposit(self, request):

        amount = request.data.get("amount")

        if not amount:
            return Response({"error": "Amount required"}, status=400)

        order_id = str(uuid.uuid4())

        payload = {
            "amount": str(amount),
            "currency": "USD",
            "order_id": order_id,
            "url_return": "http://localhost:5173/wallet",
            "url_callback": "http://localhost:8000/api/wallet/cryptomus-webhook/",
        }

        headers = {
            "merchant": settings.CRYPTOMUS_MERCHANT_ID,
            "sign": settings.CRYPTOMUS_API_KEY,
        }

        response = requests.post(settings.CRYPTOMUS_URL, json=payload, headers=headers)
        data = response.json()

        WalletTransaction.objects.create(
            user=request.user,
            amount=amount,
            type="crypto",
            status="pending",
            reference=order_id,
        )

        return Response({
            "payment_url": data["result"]["url"]
        })
    @action(detail=False, methods=['POST'])
    def checkdownload(self, request):
        user = request.user
        software_id = request.data.get('software_id')

        try:
            software = Software.objects.get(id=software_id)
            user_balance = user.balance

            if user_balance >= software.price_in_credits:

                # Deduct credits
                WalletTransaction.objects.create(
                    user=user,
                    amount=software.price_in_credits,
                    type="deduction",
                    currency='credits',
                    status='completed'
                )

                file_path = software.file.path  # your FileField
                download_url = request.build_absolute_uri(software.file.url)


                return Response({
                    "download_url": download_url
                })

            else:
                return Response(
                    {'message': 'Insufficient balance. Please add more credits.'},
                    status=402
                )

        except Software.DoesNotExist:
            return Response(
                {"message": "This software is no longer available"},
                status=404
            )

@api_view(["POST"])
@permission_classes([AllowAny])
def cryptomus_webhook(request):

    order_id = request.data.get("order_id")
    payment_status = request.data.get("status")

    try:
        transaction = WalletTransaction.objects.get(reference=order_id)
    except WalletTransaction.DoesNotExist:
        return Response(status=404)

    if payment_status == "paid":
        transaction.status = "completed"
        transaction.save()

    return Response({"ok": True})