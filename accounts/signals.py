from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WalletTransaction,User
from .utils.email import send_html_email
from django.utils.timezone import now

@receiver(post_save, sender=WalletTransaction)
def send_transaction_email(sender, instance, created, **kwargs):
    # Only send email on update, not creation
    if not created:
        subject = f"Your wallet transaction #{instance.reference} has been updated"
        template = "emails/transaction_email_template.html"
        context = {
            "transaction": instance,
            "user": instance.user,
            "current_year": now().year
        }
        send_html_email(subject, template, context, instance.user.email)
@receiver(post_save, sender=User)
def send_registration(sender, instance, created, **kwargs):
    # Only send email on update, not creation
    if  created:
        subject = f"Your Account  has been created"
        template = "emails/welcome.html"
        context = {
            "username": instance.username,
            "login_url":"https://www.volcanorom.com"
            
        }
        send_html_email(subject, template, context, instance.email)