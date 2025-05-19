from rest_framework import viewsets, status

from .models import Producto, CustomUser, Contacto, Carrito, ItemCarrito
from .serializers import ProductoSerializer, CustomUserSerializer, ContactoSerializer, CarritoSerializer, ItemCarritoSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser
from rest_framework.decorators import api_view
from django.http import JsonResponse
import mercadopago

import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django_filters.rest_framework import DjangoFilterBackend



class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    


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
    
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny  # Solo si es para pruebas

from .models import Carrito, Orden, ItemOrden
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

class CrearOrdenDesdeCarritoView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        try:
            usuario = request.user

            if not usuario or usuario.is_anonymous:
                return Response({"error": "Usuario no autenticado"}, status=status.HTTP_401_UNAUTHORIZED)

            carrito = Carrito.objects.prefetch_related('items__producto').get(cliente_id=usuario.id)

            orden = Orden.objects.create(usuario=usuario)

            for item in carrito.items.all():
                producto = item.producto

                ItemOrden.objects.create(
                    orden=orden,
                    title=producto.nombre,  # Ajustar si tu modelo usa otro campo
                    description=producto.descripcion,
                    quantity=item.cantidad,
                    currency_id="CLP",
                    unit_price=producto.precio
                )

            return Response({"mensaje": "Orden creada exitosamente", "orden_id": orden.id}, status=status.HTTP_201_CREATED)

        except Carrito.DoesNotExist:
            return Response({"error": "Carrito no encontrado para este usuario"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

from .models import Carrito, ItemCarrito, Orden, ItemOrden  # importar tus modelos
import uuid  # para generar una referencia única
from rest_framework.decorators import api_view
from django.db import transaction
from django.conf import settings


@api_view(['POST'])
def procesarpagocarrito(request):
    try:
        carrito_id = request.data.get('carrito')
        if not carrito_id:
            return Response({'error': 'ID de carrito no proporcionado.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            carrito = Carrito.objects.get(id=carrito_id)
        except Carrito.DoesNotExist:
            return Response({'error': 'Carrito no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Verificar si ya existe una orden para este carrito
        orden_existente = Orden.objects.filter(carrito=carrito).first()
        if orden_existente:
            return Response({
                'error': 'Este carrito ya tiene una orden creada.',
                'orden_id': orden_existente.id,
                'preferencia_id': orden_existente.preferencia_id
            }, status=status.HTTP_400_BAD_REQUEST)

        items_carrito = ItemCarrito.objects.filter(carrito=carrito)
        if not items_carrito.exists():
            return Response({'error': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            total = sum([item.producto.precio * item.cantidad for item in items_carrito])
            referencia = str(uuid.uuid4())[:8]

            orden = Orden.objects.create(
                carrito=carrito,
                referencia=referencia,
                total=total,
                estado='pendiente'
            )

            items_mp = []
            for item in items_carrito:
                producto = item.producto

                ItemOrden.objects.create(
                    orden=orden,
                    producto=producto,
                    nombre=producto.nombre,
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio
                )

                items_mp.append({
                    "title": producto.nombre,
                    "quantity": item.cantidad,
                    "unit_price": float(producto.precio),
                    "currency_id": "CLP"
                })

            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            preference_data = {
                "items": items_mp,
                "back_urls": {
                    "success": "http://127.0.0.1:8001/pago/success",
                    "failure": "http://127.0.0.1:8001/pago/failure",
                    "pending": "http://127.0.0.1:8001/pago/pending"
                },
                "auto_return": "approved",
                "external_reference": referencia
            }

            preference_response = sdk.preference().create(preference_data)

            if 'response' not in preference_response:
                return Response({'error': 'Error en la respuesta de Mercado Pago'}, status=500)

            preference = preference_response['response']

            if 'id' not in preference or 'init_point' not in preference:
                return Response({'error': 'Preferencia no válida de Mercado Pago'}, status=500)

            orden.preferencia_id = preference["id"]
            orden.save()

        return Response({
            "id": preference["id"],
            "init_point": preference["init_point"]
        })

    except Exception as e:
        print(f'Error procesando pago: {e}')
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def obtener_items_externos(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        items = data.get("items")

        if not items or not isinstance(items, list):
            return JsonResponse({"error": "Se requiere una lista de items válida"}, status=400)

        # Aquí puedes hacer lo que necesites con la lista 'items'
        # Por ejemplo, guardarla en base de datos o usar para otra cosa

        return JsonResponse({items})

    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

@csrf_exempt
def crear_preferencia(request):
    # Llamamos a la función externa para obtener la lista de items
    items = obtener_items_externos()

    url = "https://api.mercadopago.com/checkout/preferences"
    access_token = 'TEST-2394128164049549-050415-4700c58670e1f71e7684fa30deb4a750-1516554512'

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    body = {
        "items": items,
        "back_urls": {
            "success": "https://tuweb.com/success",
            "failure": "https://tuweb.com/failure",
            "pending": "https://tuweb.com/pending"
        },
        "auto_return": "approved"
    }

    response = requests.post(url, json=body, headers=headers)
    data = response.json()

    return JsonResponse({"preference_id": data.get("id")})

