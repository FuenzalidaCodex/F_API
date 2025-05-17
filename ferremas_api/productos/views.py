from rest_framework import viewsets, status

from .models import Producto, CustomUser, WebPayTransaction, Contacto, Carrito, ItemCarrito
from .serializers import ProductoSerializer, CustomUserSerializer, WebPayTransactionSerializer, ContactoSerializer, CarritoSerializer, ItemCarritoSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser
from rest_framework.decorators import api_view




class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    

class WebPayTransactionViewSet(viewsets.ModelViewSet):
    queryset = WebPayTransaction.objects.all()
    serializer_class = WebPayTransactionSerializer



class ContactoViewSet(viewsets.ModelViewSet):
    queryset = Contacto.objects.all()
    serializer_class = ContactoSerializer


class LoginAPIView(APIView):
    def post(self, request):
        login = request.data.get("login")
        password = request.data.get("password")

        if not login or not password:
            return Response({"error": "Faltan datos."}, status=status.HTTP_400_BAD_REQUEST)

        # Buscar usuario por username o email
        try:
            user = CustomUser.objects.get(username=login)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(email=login)
            except CustomUser.DoesNotExist:
                return Response({"error": "Usuario no encontrado."}, status=status.HTTP_401_UNAUTHORIZED)

        # Verificar la contraseña
        if not user.check_password(password):
            return Response({"error": "Contraseña incorrecta."}, status=status.HTTP_401_UNAUTHORIZED)

        # Si todo está bien, devolver info básica del usuario
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "tipo_usuario": user.tipo_usuario
        })



class CarritoViewSet(viewsets.ModelViewSet):
    queryset = Carrito.objects.all()
    serializer_class = CarritoSerializer

class ItemCarritoViewSet(viewsets.ModelViewSet):
    queryset = ItemCarrito.objects.all()
    serializer_class = ItemCarritoSerializer

from django.db.utils import IntegrityError
@api_view(['POST'])
def crear_carrito(request):
    try:
        cliente_id = request.data.get('cliente')
        if not cliente_id:
            return Response({'error': 'ID de cliente no proporcionado.'}, status=status.HTTP_400_BAD_REQUEST)

        cliente = CustomUser.objects.get(id=cliente_id)

        carrito, created = Carrito.objects.get_or_create(cliente=cliente)

        return Response(
            {
                'id': carrito.id,
                'mensaje': 'Carrito creado' if created else 'Carrito ya existente'
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    except CustomUser.DoesNotExist:
        return Response({'error': 'Cliente no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    except IntegrityError:
        return Response({'error': 'Ya existe un carrito para este usuario.'}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def agregar_item_carrito(request):
    try:
        carrito_id = request.data.get('carrito')
        producto_id = request.data.get('producto')
        cantidad = int(request.data.get('cantidad'))

        carrito = Carrito.objects.get(id=carrito_id)
        producto = Producto.objects.get(id_producto=producto_id)

        if producto.stock < cantidad:
            return Response({'error': 'Stock insuficiente'}, status=status.HTTP_400_BAD_REQUEST)

        # Buscar si el item ya existe
        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)

        if not created:
            # Si ya existía, sumar la cantidad
            item.cantidad += cantidad
        else:
            item.cantidad = cantidad

        item.save()

        return Response({'mensaje': 'Producto agregado correctamente'}, status=status.HTTP_201_CREATED)

    except Producto.DoesNotExist:
        return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Carrito.DoesNotExist:
        return Response({'error': 'Carrito no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
def listar_items_carrito(request):
    carrito_id = request.GET.get('carrito')
    items = ItemCarrito.objects.filter(carrito_id=carrito_id)
    serializer = ItemCarritoSerializer(items, many=True)
    return Response(serializer.data)