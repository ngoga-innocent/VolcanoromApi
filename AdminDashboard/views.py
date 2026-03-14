from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import WalletTransaction, User
from accounts.serializers import WalletTransactionSerializer, UserSerializer


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
        serializer = UserSerializer(data=request.data)

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
            wallet = tx.user.wallet
            wallet.balance += tx.amount
            wallet.save()

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