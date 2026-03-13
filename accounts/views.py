from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render
from django.db import models
from rest_framework.views import APIView
from django.db import transaction as db_transaction
import hashlib
import base64
import json
import requests
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
from .utils.email import send_html_email
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
            'VOLCANOROM Password Reset OTP',
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
            return Response({"error": "Invalid OTP"}, status=400)

        if not otp_record.is_valid():
            return Response({"error": "OTP expired or already used"}, status=400)

        # Pick the first matching user (or latest if multiple)
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=400)

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

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            return Response({"error": "Invalid amount"}, status=400)

        order_id = str(uuid.uuid4())

        payload = {
            "amount": str(amount),
            "currency": "USD",
            "order_id": order_id,
            "url_return": "https://volcanorom.com",
            "url_callback": settings.CRYPTOMUS_CALLBACK_URL,
        }

        payload_json = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)

        sign = hashlib.md5(
            base64.b64encode(payload_json.encode()) +
            settings.CRYPTOMUS_API_KEY.encode()
        ).hexdigest()

        headers = {
            "merchant": settings.CRYPTOMUS_MERCHANT_ID,
            "sign": sign,
            "Content-Type": "application/json"
        }

        response = requests.post(
            settings.CRYPTOMUS_URL,
            data=payload_json,
            headers=headers,
            timeout=30
        )

        print(response.text)

        if response.status_code != 200:
            return Response({"error": response.text}, status=500)

        data = response.json()

        if not data.get("result"):
            return Response({"error": "Payment creation failed"}, status=400)

        WalletTransaction.objects.create(
            user=request.user,
            amount=amount,
            type="crypto",
            status="pending",
            reference=order_id,
            # gateway_id=data["result"]["uuid"]
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

    data = request.data
    received_sign = request.headers.get("sign")

    if not received_sign:
        return Response({"error": "Missing signature"}, status=400)

    payload = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

    generated_sign = hashlib.md5(
        base64.b64encode(payload.encode()) +
        settings.CRYPTOMUS_API_KEY.encode()
    ).hexdigest()

    if generated_sign != received_sign:
        return Response({"error": "Invalid signature"}, status=400)

    order_id = data.get("order_id")
    payment_status = data.get("status")
    payment_uuid = data.get("uuid")

    if not order_id:
        return Response({"error": "Missing order_id"}, status=400)

    try:
        transaction = WalletTransaction.objects.get(reference=order_id)
    except WalletTransaction.DoesNotExist:
        return Response(status=404)

    if payment_status in ["paid", "paid_over"] and transaction.status != "completed":

        with db_transaction.atomic():
            transaction.status = "completed"
            transaction.gateway_id = payment_uuid
            transaction.save()

            user = transaction.user
            user.balance += transaction.amount
            user.save()

    return Response({"ok": True})
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_payment(request):

    order_id = request.GET.get("order_id")

    try:
        tx = WalletTransaction.objects.get(
            reference=order_id,
            user=request.user
        )
    except WalletTransaction.DoesNotExist:
        return Response({"status": "failed"})

    return Response({
        "status": tx.status
    })
class ContactView(APIView):

    def post(self, request):

        name = request.data.get("name")
        email = request.data.get("email")
        subject = request.data.get("subject")
        message = request.data.get("message")

        try:
            send_html_email(
                subject="New Contact Message",
                template="emails/contact.html",
                context={
                    "name": name,
                    "email": email,
                    "subject": subject,
                    "message": message
                },
                to_email="ngogainnocent1@gmail.com"
            )

            return Response(
                {"message": "Your message has been sent successfully."},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
@api_view(["POST"])
def p2p_price(request):

    fiat = request.data.get("fiat", "USD")

    payload = {
        "asset": "USDT",
        "fiat": fiat,
        "tradeType": "SELL",
        "page": 1,
        "rows": 5
    }

    res = requests.post(
        "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search",
        json=payload,
        timeout=30
    )

    data = res.json()

    if not data.get("data"):
        return Response({"error": "No offers found"}, status=400)

    price = float(data["data"][0]["adv"]["price"])

    return Response({
        "price": price
    })