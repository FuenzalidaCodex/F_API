from rest_framework import serializers
from .models import Producto, CustomUser, Contacto, Carrito, ItemCarrito, ItemBoleta, Boleta

class ProductoSerializer(serializers.ModelSerializer):
    id_producto = serializers.IntegerField(read_only=True)

    class Meta:
        model = Producto
        fields = ['id_producto', 'nombre', 'fabricante', 'precio', 'stock', 'descripcion', 'imagen','fecha_creacion','fecha_actualizacion','fecha_actualizacion_precio']


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'tipo_usuario', 'is_active', 'is_staff', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
    

class ContactoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contacto
        fields = '__all__'


class ItemCarritoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemCarrito
        fields = ['id', 'carrito', 'producto', 'cantidad']

class CarritoSerializer(serializers.ModelSerializer):
    items = ItemCarritoSerializer(many=True, read_only=True)

    class Meta:
        model = Carrito
        fields = ['id', 'cliente', 'items']

    def get_items(self, obj):
        items = obj.items.all()
        agrupados = {}

        for item in items:
            key = item.producto.id_producto  # clave única por producto
            if key in agrupados:
                agrupados[key]['cantidad'] += item.cantidad
            else:
                agrupados[key] = {
                    'id': item.id,
                    'carrito': item.carrito.id,
                    'producto': item.producto.id_producto,
                    'cantidad': item.cantidad
                }

        return list(agrupados.values())
    
    
class ItemBoletaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemBoleta
        fields = ['producto', 'cantidad', 'precio_unitario']

class BoletaSerializer(serializers.ModelSerializer):
    items = ItemBoletaSerializer(many=True, read_only=True)
    cliente = serializers.StringRelatedField()  # o CustomUserSerializer si quieres más info

    class Meta:
        model = Boleta
        fields = ['id', 'cliente', 'fecha', 'total', 'stripe_session_id', 'items']