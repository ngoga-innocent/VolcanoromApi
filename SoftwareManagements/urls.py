from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SoftwareViewSet, OrderViewSet

router = DefaultRouter()

router.register(r"softs", SoftwareViewSet, basename="softwares")
router.register(r"orders", OrderViewSet, basename="orders")

urlpatterns = [
    path("", include(router.urls)),
]