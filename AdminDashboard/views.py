from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import WalletTransaction, User
from accounts.serializers import WalletTransactionSerializer, UserSerializer,AdminUserSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Announcement
from .serializers import AnnouncementSerializer

class IsStaffOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Allow everyone to read
        if request.method in SAFE_METHODS:
            return True

        # Only staff can create/update/delete
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )
class AdminViewSet(viewsets.ViewSet):

    permission_classes = [IsAdminUser]

    # -------------------------
    # USERS
    # -------------------------

    @action(detail=False, methods=["get"])
    def users(self, request):
        users = User.objects.all().order_by("-date_joined")
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=["get"])
    def user(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


    @action(detail=False, methods=["post"])
    def create_user(self, request):
        serializer = AdminUserSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)


    @action(detail=True, methods=["put", "patch"])
    def update_user(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        serializer = UserSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)


    @action(detail=True, methods=["delete"])
    def delete_user(self, request, pk=None):
        try:
            user = User.objects.get(pk=pk)
            user.delete()
            return Response({"message": "User deleted"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


    # -------------------------
    # TRANSACTIONS
    # -------------------------

    @action(detail=False, methods=["get"])
    def transactions(self, request):
        txs = WalletTransaction.objects.all().order_by("-created_at")

        serializer = WalletTransactionSerializer(
            txs,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data)


    # -------------------------
    # APPROVE MANUAL DEPOSIT
    # -------------------------

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):

        try:
            tx = WalletTransaction.objects.get(pk=pk)

            if not tx.type.startswith("manual"):
                return Response({"error": "Not a manual transaction"}, status=400)

            if tx.status != "pending":
                return Response({"error": "Transaction already processed"}, status=400)

            tx.status = "completed"
            tx.save()

            # credit user wallet
            # wallet = tx.user.wallet
            # wallet.balance += tx.amount
            # wallet.save()

            return Response({"message": "Deposit approved"})

        except WalletTransaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)


    # -------------------------
    # REJECT MANUAL DEPOSIT
    # -------------------------

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):

        try:
            tx = WalletTransaction.objects.get(pk=pk)

            if not tx.type.startswith("manual"):
                return Response({"error": "Not a manual transaction"}, status=400)

            if tx.status != "pending":
                return Response({"error": "Transaction already processed"}, status=400)

            tx.status = "rejected"
            tx.save()

            return Response({"message": "Deposit rejected"})

        except WalletTransaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)


class AnnouncementViewSet(ModelViewSet):
    queryset = Announcement.objects.all().order_by("-created_at")
    serializer_class = AnnouncementSerializer
    permission_classes = [IsStaffOrReadOnly]

    def perform_create(self, serializer):
        # Deactivate all current active announcements
        Announcement.objects.filter(is_active=True).update(
            is_active=False
        )

        # Save new one as active
        serializer.save(is_active=True)

    def perform_update(self, serializer):
        instance = self.get_object()

        # If updating this announcement to active
        if self.request.data.get("is_active") in [True, "true", "True", "1"]:
            Announcement.objects.exclude(id=instance.id).filter(
                is_active=True
            ).update(is_active=False)

        serializer.save()
    @action(detail=False, methods=["get"])
    def active(self, request):
        announcement = Announcement.objects.filter(
            is_active=True
        ).first()

        if not announcement:
            return Response(None)

        serializer = self.get_serializer(announcement)
        return Response(serializer.data)