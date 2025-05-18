from rest_framework import viewsets, status

from .models import Producto, CustomUser, WebPayTransaction, Contacto, Carrito, ItemCarrito
from .serializers import ProductoSerializer, CustomUserSerializer, WebPayTransactionSerializer, ContactoSerializer, CarritoSerializer, ItemCarritoSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import mercadopago
from django.conf import settings

import requests

import requests
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend



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
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente']  # ← esto permite filtrar con ?cliente=ID


class ItemCarritoViewSet(viewsets.ModelViewSet):
    queryset = ItemCarrito.objects.all()
    serializer_class = ItemCarritoSerializer
    filterset_fields = ['carrito']  # ← necesario para filtrar por ?carrito=ID


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


@api_view(['GET'])
def convertir_moneda(request):
    moneda_destino = request.GET.get('moneda', 'USD').upper()
    tasa = obtener_tasa_conversion_de_clp(moneda_destino)
    
    if tasa:
        return Response({'tasa_conversion': tasa})
    else:
        return Response({'error': 'Tasa de conversión no disponible'}, status=status.HTTP_404_NOT_FOUND)

def obtener_tasa_conversion_de_clp(moneda_destino):
    api_key = "f4b8b0b92ab42e8171840fad"
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/CLP"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data['conversion_rates'].get(moneda_destino)
        else:
            return None
    except Exception as e:
        return None
    

# Configuración de Webpay de prueba (ambiente de integración)
COMMERCE_CODE = "597055555532"
API_KEY = "579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C"
BASE_URL = "https://webpay3gint.transbank.cl/rswebpaytransaction/api/webpay/v1.2"
# URL a la que WebPay redirige después del pago
RETURN_URL = "http://127.0.0.1:8001/web/webpay-response"


class WebpayCreateManualView(APIView):
    def post(self, request):
        try:
            # Obtener el monto del request o usar un valor por defecto
            amount = request.data.get("amount", 10000)
            buy_order = str(uuid.uuid4())[:26]
            session_id = str(uuid.uuid4())[:61]
            
            headers = {
                "Tbk-Api-Key-Id": COMMERCE_CODE,
                "Tbk-Api-Key-Secret": API_KEY,
                "Content-Type": "application/json"
            }
            
            data = {
                "buy_order": buy_order,
                "session_id": session_id,
                "amount": amount,
                "return_url": RETURN_URL
            }
            
            response = requests.post(f"{BASE_URL}/transactions", json=data, headers=headers)
            
            if response.status_code != 200:
                return Response({
                    "error": f"{response.status_code} {response.reason} for url: {response.url}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            res_json = response.json()
            
            # Crear la transacción en la base de datos con los campos correctos
            transaction = WebPayTransaction(
                token=res_json["token"],
                buy_order=buy_order,
                session_id=session_id,
                amount=amount,
                status="INITIALIZED"
            )
            transaction.save()
            
            return Response({
                "url": res_json["url"],
                "token": res_json["token"]
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            import traceback
            traceback.print_exc()  # Imprime el error completo en la consola del servidor
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class WebpayCommitManualView(APIView):
    def post(self, request):
        try:
            token = request.data.get("token_ws")
            if not token:
                return Response({"error": "Token no proporcionado"}, status=status.HTTP_400_BAD_REQUEST)
                
            headers = {
                "Tbk-Api-Key-Id": COMMERCE_CODE,
                "Tbk-Api-Key-Secret": API_KEY,
                "Content-Type": "application/json"
            }
            
            response = requests.put(f"{BASE_URL}/transactions/{token}", headers=headers)
            
            if response.status_code != 200:
                return Response({
                    "error": f"{response.status_code} {response.reason} for url: {response.url}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
            # Actualizar el estado de la transacción en la base de datos
            try:
                transaction = WebPayTransaction.objects.get(token=token)
                transaction.status = "COMPLETED"
                transaction.save()
            except WebPayTransaction.DoesNotExist:
                pass  # Si no existe la transacción, continuar de todos modos
                
            return Response(response.json(), status=response.status_code)
            
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
