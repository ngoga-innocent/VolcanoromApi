from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order
from accounts.utils.email import send_html_email
from django.utils.timezone import now

@receiver(post_save, sender=Order)
def send_order_status_email(sender, instance: Order, created, **kwargs):
    if created:
        # Don't send on creation
        return

    # Only send email if status changed
    if "update_fields" in kwargs and kwargs["update_fields"] and "status" not in kwargs["update_fields"]:
        return

    subject = f"Your Order #{instance.id} Status Update"
    template = "emails/order_status_email.html"
    context = {
        "transaction": instance,
        "user": instance.user,
        "current_year": now().year
    }
    send_html_email(subject, template, context, instance.user.email)