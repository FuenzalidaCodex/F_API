from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductoViewSet, UsuarioViewSet, WebPayTransactionViewSet, ContactoViewSet
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from . import views

router = DefaultRouter()
router.register(r'productos', ProductoViewSet)
router.register(r'usuarios', UsuarioViewSet)
router.register(r'transacciones', WebPayTransactionViewSet)
router.register(r'contactos', ContactoViewSet)

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
    path('login/', views.user_login, name='login'),
    # JWT Auth
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Documentación Swagger UI
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]