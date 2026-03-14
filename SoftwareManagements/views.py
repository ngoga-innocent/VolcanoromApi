from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .models import Software, SoftwareImage, Order
from .serializers import SoftwareSerializer, OrderSerializer
from django.db import transaction
from accounts.models import WalletTransaction

# SOFTWARE VIEWSET
class SoftwareViewSet(ModelViewSet):

    queryset = Software.objects.all().order_by("-created_at")
    serializer_class = SoftwareSerializer

    def get_permissions(self):

        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser,IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        print("uploaded by",self.request.user)
        software = serializer.save(uploaded_by=self.request.user)

        images = self.request.FILES.getlist("images")

        if images:
            for img in images:
                SoftwareImage.objects.create(
                software=software,
                image=img
                )

    def perform_update(self, serializer):

        software = serializer.save()

        images = self.request.FILES.getlist("images")

        if images:

            SoftwareImage.objects.filter(
                software=software
            ).delete()

            for img in images:
                SoftwareImage.objects.create(
                    software=software,
                    image=img
                )


# ORDER VIEWSET
class OrderViewSet(ModelViewSet):

    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer

    def get_permissions(self):

        if self.action == "create":
            permission_classes = [IsAuthenticated]

        elif self.action in ["complete_order", "cancel_order"]:
            permission_classes = [IsAdminUser]

        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_queryset(self):

        user = self.request.user

        if user.is_staff:
            return Order.objects.all().order_by("-created_at")

        return Order.objects.filter(user=user).order_by("-created_at")

    def perform_create(self, serializer):

        user = self.request.user
        software = serializer.validated_data["software"]
        price_to_pay=serializer.validated_data['price_paid']
        price = software.price_in_credits

        # check balance using property
        if user.balance < price_to_pay:
            raise ValidationError({
                "error": "Insufficient credits to place this order"
            })

        # prevent duplicate pending orders
        if Order.objects.filter(
            user=user,
            software=software,
            status="pending"
        ).exists():

            raise ValidationError({
                "error": "You already have a pending order for this software"
            })

        with transaction.atomic():

            order = serializer.save(
                user=user,
                price_paid=price_to_pay
            )

            # create deduction transaction
            WalletTransaction.objects.create(
                user=user,
                amount=price_to_pay,
                type="deduction",
                status="completed",
                reference=f"Order #{order.id}"
            )
    @action(detail=True, methods=["post"])
    def complete_order(self, request, pk=None):

        order = self.get_object()

        order.download_link = request.data.get("download_link")
        order.license_key = request.data.get("license_key")
        order.admin_note = request.data.get("admin_note")

        order.status = "completed"
        order.save()

        return Response({
            "message": "Order completed successfully"
        })

    # ADMIN CANCELS ORDER + REFUND
    @action(detail=True, methods=["post"])
    def cancel_order(self, request, pk=None):

        order = self.get_object()

        if order.status == "completed":
            return Response(
                {"error": "Completed orders cannot be cancelled"},
                status=400
            )

        user = order.user

        with transaction.atomic():

            WalletTransaction.objects.create(
                user=user,
                amount=order.price_paid,
                type="manual",
                status="completed",
                reference=f"Refund for order #{order.id}"
            )

            order.status = "cancelled"
            order.save()

        return Response({
            "message": "Order cancelled and credits refunded"
        })