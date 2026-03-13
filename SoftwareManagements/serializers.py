from rest_framework import serializers
from .models import SoftwareImage,Software
class SoftwareImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = SoftwareImage
        fields = ("id", "image")
class SoftwareSerializer(serializers.ModelSerializer):

    images = SoftwareImageSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Software
        fields = (
            "id",
            "name",
            "description",
            "type",
            "file",
            "price_in_credits",
            "thumbnail",
            "images",
            "created_at",
        )
    