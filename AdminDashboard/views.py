from rest_framework import viewsets, status
from rest_framework.permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import WalletTransaction, User
from accounts.serializers import WalletTransactionSerializer, UserSerializer

class AdminViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["get"])
    def users(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def transactions(self, request):
        txs = WalletTransaction.objects.all().order_by("-created_at")
        serializer = WalletTransactionSerializer(txs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        try:
            tx = WalletTransaction.objects.get(pk=pk, type="manual")
            if tx.status != "pending":
                return Response({"error": "Transaction already processed"}, status=400)
            tx.status = "completed"
            tx.save()

            # Update user balance
            # tx.user.wallet.balance += tx.amount
            # tx.user.wallet.save()

            return Response({"message": "Deposit approved"})
        except WalletTransaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        try:
            tx = WalletTransaction.objects.get(pk=pk, type="manual")
            if tx.status != "pending":
                return Response({"error": "Transaction already processed"}, status=400)
            tx.status = "rejected"
            tx.save()
            return Response({"message": "Deposit rejected"})
        except WalletTransaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=404)