from rest_framework.routers import DefaultRouter
from .views import AuthViewSet,WalletViewSet,ContactView
from django.urls import path
router = DefaultRouter()
router.register('auth', AuthViewSet, basename='auth')
router.register('wallet',WalletViewSet,basename='wallet')

urlpatterns = router.urls
urlpatterns+=[
    path('contact',ContactView.as_view())
]