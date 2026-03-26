from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name=models.CharField(max_length=255)
class Software(models.Model):

    SOFTWARE_TYPES = (
        ("mdm_files", "MDM Files"),
        ("tools", "Tools"),
        ("services","Services")
    )

    SERVICE_TYPES = (
        ("imei", "IMEI Service"),
        ("server", "Server Service"),
        ("remote", "Remote Service"),
    )

    name = models.CharField(max_length=255)

    description = models.TextField()

    type = models.CharField(
        max_length=20,
        choices=SOFTWARE_TYPES
    )

    price_in_credits = models.PositiveIntegerField()

    thumbnail = models.ImageField(
        upload_to="software/thumbnails/"
    )

    # TOOL ONLY
    duration = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    service = models.CharField(
        max_length=50,
        choices=SERVICE_TYPES,
        blank=True,
        null=True
    )

    client_fields = models.JSONField(
    default=list,
    blank=True,
    help_text='Example: [{"name": "IMEI", "type": "text"}, {"name": "Screenshot", "type": "image"}]')

    # MDM FILE ONLY
    download_link = models.URLField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

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

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    software = models.ForeignKey(
        Software,
        on_delete=models.CASCADE
    )

    price_paid = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    # CLIENT SUBMITTED DATA
    client_data = models.JSONField(
        default=dict,
        blank=True
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

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user} - {self.software.name}"
class OrderClientFile(models.Model):
    order = models.ForeignKey(
        Order,
        related_name="files",
        on_delete=models.CASCADE
    )

    field_name = models.CharField(max_length=255)

    file = models.ImageField(upload_to="orders/client_files/")

    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order.id} - {self.field_name}"
class SoftwareImage(models.Model):

    software = models.ForeignKey(
        Software,
        related_name="images",
        on_delete=models.CASCADE
    )

    image = models.ImageField(upload_to="software/gallery/")