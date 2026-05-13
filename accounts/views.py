from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
# from django.shortcuts import render
from django.db import models
from rest_framework.views import APIView
from django.db import transaction as db_transaction
import hashlib
import base64
import random
import json
from django.utils import timezone
from rest_framework.permissions import IsAdminUser
from datetime import timedelta
from django.core.mail import send_mail
from rest_framework import generics, permissions
from .models import HeroCarousel
from .serializers import HeroCarouselSerializer
import requests
from .serializers import (
    RegisterSerializer, LoginSerializer,DepositSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,UserProfileSerializer,AdminDepositSerializer
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
from .serializers import WalletTransactionSerializer
import pyotp
import qrcode
import base64
import logging
from io import BytesIO

# from django.http import FileResponse
import os
logger = logging.getLogger(__name__)
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
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def setup_mfa(self, request):
        user = request.user

        try:
            # 🔐 Prevent re-enabling if already active
            if user.mfa_enabled:
                return Response(
                    {"error": "MFA already enabled"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate secret
            secret = pyotp.random_base32()
            user.otp_secret = secret
            user.save()

            # Create provisioning URI
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(
                name=user.email or user.username,
                issuer_name="VOLCANOROM"
            )

            # Generate QR code
            qr = qrcode.make(uri)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()

            return Response({
                "qr_code": f"data:image/png;base64,{qr_base64}",
                "secret": secret  # optional
            })

        except Exception as e:
            # 🔥 Log full error for debugging
            logger.error(f"MFA setup failed for user {user.id}: {str(e)}")

            return Response(
                {"error": "Failed to initialize MFA. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def send_email_otp(self, request):
        user = request.user

        try:
            otp = str(random.randint(100000, 999999))

            user.email_otp = otp
            user.email_otp_expires = timezone.now() + timedelta(minutes=5)
            user.save()

            send_mail(
                subject="VOLCANOROM Verification Code",
                message=f"""
                Your verification code is:

                {otp}

                This code expires in 5 minutes.
                            """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({
                "message": "OTP sent successfully"
            })

        except Exception as e:
            logger.error(f"Email OTP failed for user {user.id}: {str(e)}")

            return Response(
                {"error": "Failed to send OTP"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def verify_email_backup(self, request):
        user = request.user
        otp = request.data.get("otp")

        try:
            if not otp:
                return Response(
                    {"error": "OTP is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not user.email_otp:
                return Response(
                    {"error": "No OTP requested"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if timezone.now() > user.email_otp_expires:
                return Response(
                    {"error": "OTP expired"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if user.email_otp != otp:
                return Response(
                    {"error": "Invalid OTP"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # CLEAR OTP
            user.email_otp = None
            user.email_otp_expires = None
            user.save()

            return Response({
                "message": "Email verification successful"
            })

        except Exception as e:
            logger.error(f"Email backup MFA failed for user {user.id}: {str(e)}")

            return Response(
                {"error": "Verification failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def verify_mfa(self, request):
        user = request.user

        try:
            otp = request.data.get("otp")
            print(otp)
            # 🔐 Validate OTP presence
            if not otp:
                return Response(
                    {"error": "OTP is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 🔐 Ensure MFA setup started
            

            # 🔐 Verify OTP (allow small time drift)
            totp = pyotp.TOTP(user.otp_secret)
            print(totp.now())
            if not totp.verify(otp, valid_window=1):
                return Response(
                    {"error": "Invalid or expired OTP"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # ✅ Enable MFA
            if not user.mfa_enabled:
                user.mfa_enabled = True
                user.save()

            return Response({"message": "MFA enabled successfully"})

        except Exception as e:
            logger.error(f"MFA verification failed for user {user.id}: {str(e)}")

            return Response(
                {"error": "Failed to verify MFA. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
# Wallet View Set
class WalletViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    @action(detail=False, methods=["get"])
    def transactions(self, request):
        user=request.user
        txs = WalletTransaction.objects.filter(user=user).order_by("-created_at")

        serializer = WalletTransactionSerializer(
            txs,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data)

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
            type=serializer.validated_data["type"],
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
            "currency": "USDT",
            "order_id": order_id,
            "url_return": "https://volcanorom.com",
            "url_callback": settings.CRYPTOMUS_CALLBACK_URL,
            "lifetime":300,
            "url_return":'https://volcanorom.com/deposit',
            "url_success":'https://volcanorom.com/',
            "is_payment_multiple":True
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
            timeout=30,
          
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
class AdminDepositView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = AdminDepositSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        transaction = serializer.save()

        return Response(
            {
                "message": "Wallet funded successfully",
                "transaction_id": transaction.id,
            },
            status=status.HTTP_201_CREATED,
        )
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

    fiat = request.data.get("fiat", "USDT")

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
# PUBLIC (frontend uses this)
class ActiveHeroCarouselView(generics.ListAPIView):
    serializer_class = HeroCarouselSerializer

    def get_queryset(self):
        return HeroCarousel.objects.filter(is_active=True).order_by("order")


# ADMIN CRUD
class HeroCarouselListCreateView(generics.ListCreateAPIView):
    queryset = HeroCarousel.objects.all().order_by("order")
    serializer_class = HeroCarouselSerializer
    permission_classes = [permissions.IsAdminUser]


class HeroCarouselDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = HeroCarousel.objects.all()
    serializer_class = HeroCarouselSerializer
    permission_classes = [permissions.IsAdminUser]
