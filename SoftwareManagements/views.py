from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Software,SoftwareImage
from .serializers import SoftwareSerializer

class SoftwareViewSet(ModelViewSet):

    queryset = Software.objects.all().order_by("-created_at")
    serializer_class = SoftwareSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):

        software = serializer.save(uploaded_by=self.request.user)

        # Multiple images upload
        images = self.request.FILES.getlist("images")

        for img in images:
            SoftwareImage.objects.create(
                software=software,
                image=img
            )

    def perform_update(self, serializer):

        software = serializer.save()

        # Optional: update gallery images if provided
        images = self.request.FILES.getlist("images")

        if images:
            # Delete old images if you want clean update
            SoftwareImage.objects.filter(
                software=software
            ).delete()

            for img in images:
                SoftwareImage.objects.create(
                    software=software,
                    image=img
                )