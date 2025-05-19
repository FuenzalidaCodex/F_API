from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet, UsuarioViewSet, ContactoViewSet, CarritoViewSet, ItemCarritoViewSet, crear_carrito, agregar_item_carrito
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import convertir_moneda
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from .views import LoginAPIView
from . import views
from .views import crear_preferencia
from .views import CrearOrdenDesdeCarritoView

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'usuarios', UsuarioViewSet)
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
    path('crear_orden_desde_carrito/', CrearOrdenDesdeCarritoView.as_view(), name='crear_orden'),
    path('crear_preferencia', crear_preferencia, name='crear_preferencia'),
    path('procesarpagocarrito/', views.procesarpagocarrito, name='procesarpagocarrito'),
    path('conversion/', convertir_moneda, name='conversion_moneda'),
    path('crear-carrito/', crear_carrito),
    path('agregar-item/', agregar_item_carrito),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]