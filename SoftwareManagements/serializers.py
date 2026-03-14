from rest_framework import serializers
from .models import SoftwareImage, Software,Order
from accounts.serializers import UserSerializer

class SoftwareImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = SoftwareImage
        fields = ("id", "image")


class SoftwareSerializer(serializers.ModelSerializer):

    class Meta:
        model = Software
        fields = "__all__"
        read_only_fields = ["uploaded_by"]
class OrderSerializer(serializers.ModelSerializer):

    software_details = SoftwareSerializer(source="software", read_only=True)
    user_details = UserSerializer(source="user", read_only=True)

    class Meta:
        model = Order
        fields = "__all__"

        read_only_fields = [
            "user",
            "download_link",
            "license_key",
            "admin_note",
            "status",
        ]