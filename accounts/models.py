from django.contrib.auth.models import AbstractUser
from django.db import models
# from phonenumber_field.modelfields import PhoneNumberField  # optional
from django.conf import settings
import random
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    phone_number = models.CharField(null=True,blank=True,max_length=255)

    def __str__(self):
        return self.username

    @property
    def balance(self):
        # from .wallet import WalletTransaction  # import here to avoid circular import
        total_in = WalletTransaction.objects.filter(
            user=self, type__in=['manual', 'crypto'], status__in=['approved','completed']
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0

        total_out = WalletTransaction.objects.filter(
            user=self, type='deduction', status='completed'
        ).aggregate(models.Sum('amount'))['amount__sum'] or 0

        return total_in - total_out


class WalletTransaction(models.Model):
    TRANSACTION_TYPE = (
        ('manual_lumicash', 'Manual Payment'),
        ('manual_mpesa', 'Manual MPesa Payment'),
        ('manual_safaricom', 'Manual SafariCom Payment'),
        ('crypto', 'Crypto Payment'),
        ('deduction', 'Tool Download Deduction'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),  # for crypto/manual once verified
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet_transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=30, choices=TRANSACTION_TYPE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    proof = models.FileField(upload_to='wallet_proofs/', null=True, blank=True)
    currency=models.CharField(max_length=200,null=True,blank=True)
    reference = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.type} - {self.amount}"


class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    verified = models.BooleanField(default=False)

    def is_valid(self):
        return not self.verified and (timezone.now() - self.created_at) < timedelta(minutes=10)

    @staticmethod
    def generate_otp():
        return str(random.randint(100000, 999999))
class HeroCarousel(models.Model):
    title = models.CharField(max_length=255, blank=True, null=True)
    subtitle = models.TextField(blank=True, null=True)

    image = models.ImageField(upload_to="hero_carousel/")
    is_active = models.BooleanField(default=True)

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Slide {self.id}"