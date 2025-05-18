from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet, UsuarioViewSet, WebPayTransactionViewSet, ContactoViewSet, CarritoViewSet, ItemCarritoViewSet, crear_carrito, agregar_item_carrito
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import convertir_moneda
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from .views import LoginAPIView
from .views import WebpayCreateManualView, WebpayCommitManualView

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'transacciones', WebPayTransactionViewSet)
router.register(r'contactos', ContactoViewSet)
router.register(r'carrito', CarritoViewSet)
router.register(r'items-carrito', ItemCarritoViewSet)

schema_view = get_schema_view(
   openapi.Info(
      title="Ferremas API",
      default_version='v1',
      description="API para gestión de ferretería Ferremas",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('', include(router.urls)),
    path('webpay/create/', WebpayCreateManualView.as_view(), name='webpay-create'),
    path('webpay/commit/', WebpayCommitManualView.as_view(), name='webpay-commit'),
    path('conversion/', convertir_moneda, name='conversion_moneda'),
    path('crear-carrito/', crear_carrito),
    path('agregar-item/', agregar_item_carrito),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]