from rest_framework.routers import DefaultRouter
from .views import AdminViewSet,AnnouncementViewSet

router = DefaultRouter()
router.register('', AdminViewSet, basename='dashboard')
router.register("announcements", AnnouncementViewSet)

urlpatterns = router.urls