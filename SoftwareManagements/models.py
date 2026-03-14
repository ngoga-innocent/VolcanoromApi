from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name=models.CharField(max_length=255)
class Software(models.Model):

    SOFTWARE_TYPES = (
        ('mdm_files', 'MDM Files'),
        ('tools', 'Tools'),
    )

    name = models.CharField(max_length=255)
    description = models.TextField()

    type = models.CharField(
        max_length=20,
        choices=SOFTWARE_TYPES
    )

    price_in_credits = models.PositiveIntegerField()

    thumbnail = models.ImageField(upload_to="software/thumbnails/")

    # durations offered
    duration_options = models.JSONField(
        default=list,
        help_text="Example: ['1 Month','3 Months','6 Months']"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name
class Order(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("completed", "Completed"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    software = models.ForeignKey(
        Software,
        on_delete=models.CASCADE
    )

    duration = models.CharField(max_length=50)

    price_paid = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    # ADMIN RESPONSE
    download_link = models.URLField(
        blank=True,
        null=True
    )

    license_key = models.TextField(
        blank=True,
        null=True
    )

    admin_note = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
class SoftwareImage(models.Model):

    software = models.ForeignKey(
        Software,
        related_name="images",
        on_delete=models.CASCADE
    )

    image = models.ImageField(upload_to="software/gallery/")