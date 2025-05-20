from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

# Create your models here.

class Categoria_Producto(models.Model): 
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    def __str__(self): 
        return self.nombre 
        
class Ferretería(models.Model):
    codigo_ferretería = models.AutoField(primary_key=True)
    nombre_ferretería = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre_ferretería


class Producto(models.Model):
    id_producto=models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    fabricante = models.CharField(max_length=50, default="Desconocido")
    ferretería = models.ForeignKey(Ferretería, on_delete=models.CASCADE, related_name='productos', default=1)
    categoria = models.ForeignKey(Categoria_Producto, on_delete=models.CASCADE, related_name='productos', default=1)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    stock = models.IntegerField()
    descripcion = models.TextField(blank=True, null=True)
    imagen = models.ImageField(upload_to="productos", null=True, blank=True)
    currency_id = models.CharField(max_length=10, default="CLP")

    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_actualizacion_precio = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.pk:
            # Obtenemos el producto anterior para comparar el precio
            original = Producto.objects.get(pk=self.pk)
            if original.precio != self.precio:
                self.fecha_actualizacion_precio = timezone.now()
        else:
            # Si es un nuevo producto, establecemos la fecha de actualización de precio
            self.fecha_actualizacion_precio = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('cliente', 'Cliente'),
        ('vendedor', 'Vendedor'),
        ('bodeguero', 'Bodeguero'),
        ('contador', 'Contador'),
    )
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    tipo_usuario = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='cliente')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email
    
class Contacto(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20, blank=True)
    mensaje = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mensaje de {self.nombre}"


class Carrito(models.Model):
    cliente = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='carrito')

    def __str__(self):
        return f"Carrito de {self.cliente.username}"


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en carrito de {self.carrito.cliente.username}"
    

class Orden(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ordenes')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Orden #{self.id} de {self.usuario.username}"


class ItemOrden(models.Model):
    orden = models.ForeignKey(Orden, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    currency_id = models.CharField(max_length=10)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.title} (x{self.quantity}) - {self.orden.usuario.username}"
    

class Boleta(models.Model):
    cliente = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)

class ItemBoleta(models.Model):
    boleta = models.ForeignKey(Boleta, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    



