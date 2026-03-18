from rest_framework.routers import DefaultRouter
from .views import AuthViewSet,WalletViewSet,ContactView,p2p_price,check_payment,cryptomus_webhook
from .views import *
from django.urls import path
router = DefaultRouter()
router.register('auth', AuthViewSet, basename='auth')
router.register('wallet',WalletViewSet,basename='wallet')

urlpatterns = router.urls
urlpatterns+=[
    path('contact',ContactView.as_view()),
    path("p2p-price/", p2p_price),
    path("check-payment/", check_payment),
    path("cryptomus-webhook/", cryptomus_webhook),
     path("hero-carousel/", ActiveHeroCarouselView.as_view()),

    # ADMIN
    path("admin/hero-carousel/", HeroCarouselListCreateView.as_view()),
    path("admin/hero-carousel/<int:pk>/", HeroCarouselDetailView.as_view()),
    
]