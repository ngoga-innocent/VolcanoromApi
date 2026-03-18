from rest_framework import serializers
from .models import SoftwareImage, Software,Order,OrderClientFile
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


class OrderClientFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderClientFile
        fields = "__all__"
class OrderSerializer(serializers.ModelSerializer):
    files = OrderClientFileSerializer(many=True, read_only=True)
    client_full_data = serializers.SerializerMethodField()
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
    def get_client_full_data(self, obj):
        data = obj.client_data or {}

        for file in obj.files.all():
            data[file.field_name] = file.file.url

        return data