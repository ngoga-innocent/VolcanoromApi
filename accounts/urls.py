from rest_framework.routers import DefaultRouter
from .views import AuthViewSet,WalletViewSet

router = DefaultRouter()
router.register('auth', AuthViewSet, basename='auth')
router.register('wallet',WalletViewSet,basename='wallet')
urlpatterns = router.urls