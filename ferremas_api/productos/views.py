from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

import json
import requests
import stripe

from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.utils import IntegrityError

from .models import (
    Producto, CustomUser, Contacto, Carrito,
    ItemCarrito, Boleta
)
from .serializers import (
    ProductoSerializer, CustomUserSerializer,
    ContactoSerializer, CarritoSerializer,
    ItemCarritoSerializer, BoletaSerializer
)





class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer


class ContactoViewSet(viewsets.ModelViewSet):
    queryset = Contacto.objects.all()
    serializer_class = ContactoSerializer


class CarritoViewSet(viewsets.ModelViewSet):
    queryset = Carrito.objects.all()
    serializer_class = CarritoSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['cliente']


class ItemCarritoViewSet(viewsets.ModelViewSet):
    queryset = ItemCarrito.objects.all()
    serializer_class = ItemCarritoSerializer
    filterset_fields = ['carrito']


class BoletaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Boleta.objects.all()
    serializer_class = BoletaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        return Boleta.objects.filter(cliente=usuario)





class LoginAPIView(APIView):
    def post(self, request):
        login = request.data.get("login")
        password = request.data.get("password")

        if not login or not password:
            return Response({"error": "Faltan datos."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(username=login)
        except CustomUser.DoesNotExist:
            try:
                user = CustomUser.objects.get(email=login)
            except CustomUser.DoesNotExist:
                return Response({"error": "Usuario no encontrado."}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            return Response({"error": "Contraseña incorrecta."}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "tipo_usuario": user.tipo_usuario
        })


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

        item, created = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)

        if not created:
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


@api_view(['DELETE'])
def eliminar_item_carrito(request):
    try:
        carrito_id = request.data.get('carrito')
        producto_id = request.data.get('producto')

        item = ItemCarrito.objects.get(carrito_id=carrito_id, producto_id=producto_id)
        item.delete()

        return Response({'mensaje': 'Producto eliminado del carrito'}, status=status.HTTP_200_OK)
    except ItemCarrito.DoesNotExist:
        return Response({'error': 'Item no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
def vaciar_carrito(request, carrito_id):
    try:
        carrito = Carrito.objects.get(id=carrito_id)
        carrito.items.all().delete()
        carrito.delete()
        return Response({'mensaje': 'Carrito vaciado y eliminado'}, status=status.HTTP_200_OK)
    except Carrito.DoesNotExist:
        return Response({'error': 'Carrito no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        return None
    except Exception:
        return None


@api_view(['GET'])
def api_url_view(request):
    host = request.get_host()
    return Response({"api_url": f"http://{host}/api/"})


class StripeLineItemsView(APIView):
    def get(self, request, cliente_id):
        try:
            carrito = Carrito.objects.get(cliente_id=cliente_id)
            items = ItemCarrito.objects.filter(carrito=carrito)

            if not items.exists():
                return Response({"error": "El carrito está vacío."}, status=status.HTTP_400_BAD_REQUEST)

            line_items = []

            for item in items:
                producto = item.producto
                if not producto:
                    continue

                line_items.append({
                    "price_data": {
                        "currency": "clp",
                        "product_data": {
                            "name": producto.nombre
                        },
                        "unit_amount": int(producto.precio * 100)
                    },
                    "quantity": item.cantidad
                })

            return Response({"line_items": line_items}, status=status.HTTP_200_OK)

        except Carrito.DoesNotExist:
            return Response({"error": "Carrito no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def crear_sesion_pago(request):
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        carrito_items = request.data.get('items', [])

        line_items = []
        for item in carrito_items:
            line_items.append({
                'price_data': {
                    'currency': 'clp',
                    'unit_amount': int(item['precio']) * 100,
                    'product_data': {
                        'name': item['nombre'],
                    },
                },
                'quantity': item['cantidad'],
            })

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f"{settings.API_URL}/exito/",
            cancel_url=f"{settings.API_URL}/cancelado/",
            metadata={
                'cliente_id': str(request.data.get('cliente_id'))
            }
        )

        return Response({'id': session.id})

    except Exception as e:
        return Response({'error': str(e)}, status=500)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        cliente_id = session.get("metadata", {}).get("cliente_id")

        if cliente_id:
            try:
                cliente = CustomUser.objects.get(id=cliente_id)
                carrito = Carrito.objects.get(cliente=cliente)
                items = ItemCarrito.objects.filter(carrito=carrito)

                for item in items:
                    item.producto.stock -= item.cantidad
                    item.producto.save()

                items.delete()
                carrito.delete()

            except Exception as e:
                return HttpResponse(status=500)

    return HttpResponse(status=200)


def admin_view(request):
    usuarios = CustomUser.objects.all()
    return render(request, 'empleados/admin.html', {'usuarios': usuarios})



@api_view(['GET', 'POST'])
def enviar_email_con_emailjs(request):
    if request.method == 'POST':
        nombre = request.data.get('nombre')
        email = request.data.get('email')
    else:  # GET
        nombre = request.query_params.get('nombre')
        email = request.query_params.get('email')

    if not nombre or not email:
        return Response({'error': 'Faltan datos'}, status=status.HTTP_400_BAD_REQUEST)

    EMAILJS_SERVICE_ID = 'service_4amfijq300903'
    EMAILJS_TEMPLATE_ID = 'template_p9qam3n'
    EMAILJS_PUBLIC_KEY = '_szGv0_6TI62n2zCR'

    payload = {
        'service_id': EMAILJS_SERVICE_ID,
        'template_id': EMAILJS_TEMPLATE_ID,
        'user_id': EMAILJS_PUBLIC_KEY,
        'template_params': {
            'nombre': nombre,
            'correo': email,
        }
    }

    try:
        response = requests.post(
            'https://api.emailjs.com/api/v1.0/email/send',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )

        if response.status_code == 200:
            return Response({'mensaje': 'Correo enviado correctamente'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Error al enviar correo', 'detalle': response.text}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)