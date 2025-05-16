from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from .models import Producto, CustomUser, WebPayTransaction
from .serializers import ProductoSerializer, CustomUserSerializer, WebPayTransactionSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [AllowAny]  # Registro abierto
        else:
            permission_classes = [IsAuthenticated]  # Solo autenticados para listar, modificar, eliminar
        return [permission() for permission in permission_classes]
    

class WebPayTransactionViewSet(viewsets.ModelViewSet):
    queryset = WebPayTransaction.objects.all()
    serializer_class = WebPayTransactionSerializer
