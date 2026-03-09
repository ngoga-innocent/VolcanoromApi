from rest_framework.routers import DefaultRouter
from .views import AdminViewSet

router = DefaultRouter()
router.register('', AdminViewSet, basename='dashboard')

urlpatterns = router.urls