from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Category(models.Model):
    name=models.CharField(max_length=255)
class Software(models.Model):
    software_choices=(('mdm files','Mdm Files'),('tools',"Tools"))
    name = models.CharField(max_length=255)
    description = models.TextField()

    price_in_credits = models.PositiveIntegerField()
    type=models.CharField(choices=software_choices,default='tools')
    thumbnail = models.ImageField(upload_to="software/thumbnails/")
    file = models.FileField(upload_to="software/files/",null=True,blank=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name
class SoftwareImage(models.Model):

    software = models.ForeignKey(
        Software,
        related_name="images",
        on_delete=models.CASCADE
    )

    image = models.ImageField(upload_to="software/gallery/")