from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from .views import (
    ProductoViewSet,
    UsuarioViewSet,
    ContactoViewSet,
    CarritoViewSet,
    ItemCarritoViewSet,
    crear_carrito,
    agregar_item_carrito,
    convertir_moneda,
    LoginAPIView,
    api_url_view,
    eliminar_item_carrito,
    vaciar_carrito,
    crear_sesion_pago,
    StripeLineItemsView,
    stripe_webhook,
    BoletaViewSet,
    admin_view
)

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'contactos', ContactoViewSet)
router.register(r'carrito', CarritoViewSet)
router.register(r'items-carrito', ItemCarritoViewSet)
router.register(r'boletas', BoletaViewSet, basename='boleta')

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
    path("get-url/", api_url_view),
    path('admin-usuarios/', admin_view, name='admin_usuarios'),
    path('webhook/stripe/', stripe_webhook, name='stripe-webhook'),
    path('api/carrito/stripe-line-items/<int:cliente_id>/', StripeLineItemsView.as_view(), name='stripe-line-items'),
    path('pago/stripe/', crear_sesion_pago, name='pago_stripe'),
    path('eliminar-item/', eliminar_item_carrito),
    path('vaciar-carrito/<int:carrito_id>/', vaciar_carrito),
    path('conversion/', convertir_moneda, name='conversion_moneda'),
    path('crear-carrito/', crear_carrito),
    path('agregar-item/', agregar_item_carrito),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]