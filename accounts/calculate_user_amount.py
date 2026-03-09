from django.db.models import Sum
from .models import WalletTransaction
def get_user_balance(user):
    total_in = WalletTransaction.objects.filter(
        user=user, type__in=['manual', 'crypto'], status__in=['approved','completed']
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    total_out = WalletTransaction.objects.filter(
        user=user, type='deduction', status='completed'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return total_in - total_out