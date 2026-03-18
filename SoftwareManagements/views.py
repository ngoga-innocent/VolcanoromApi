from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .models import Software, SoftwareImage, Order,OrderClientFile
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
        price_to_pay = serializer.validated_data["price_paid"]

        # 🔒 Validate balance
        if user.balance < price_to_pay:
            raise ValidationError({
                "error": "Insufficient credits to place this order"
            })

        # 🚫 Prevent duplicate pending orders
        if Order.objects.filter(
            user=user,
            software=software,
            status="pending"
        ).exists():
            raise ValidationError({
                "error": "You already have a pending order for this software"
            })

        client_fields = software.client_fields  # [{"name": "...", "type": "..."}]

        text_data = {}
        image_files = []

        # 🔥 Parse dynamic fields
        for field in client_fields:

            name = field.get("name")
            field_type = field.get("type")

            if field_type == "text":
                value = self.request.data.get(name)

                if not value:
                    raise ValidationError({name: "This field is required"})

                text_data[name] = value

            elif field_type == "image":
                file = self.request.FILES.get(name)

                if not file:
                    raise ValidationError({name: "Image is required"})

                image_files.append((name, file))

        with transaction.atomic():

            # ✅ Create order
            order = serializer.save(
                user=user,
                price_paid=price_to_pay,
                client_data=text_data
            )

            # ✅ Save uploaded images
            for field_name, file in image_files:
                OrderClientFile.objects.create(
                    order=order,
                    field_name=field_name,
                    file=file
                )

            # 💰 Deduct wallet
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
            order.admin_note = request.data.get("admin_note")
            order.status = "cancelled"
            order.save()

        return Response({
            "message": "Order cancelled and credits refunded"
        })