from django.contrib import admin
from .models import User, WalletTransaction

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone_number', 'balance', 'is_staff', 'is_superuser')

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'amount', 'status', 'created_at')
    list_filter = ('status', 'type')
    search_fields = ('user__username', 'user__email', 'reference')