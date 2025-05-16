from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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
    

class WebPayTransaction(models.Model):
    order_id = models.CharField(max_length=100)
    session_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    transaction_date = models.DateTimeField(auto_now_add=True)
    buy_order = models.CharField(max_length=100)
    authorization_code = models.CharField(max_length=20, null=True, blank=True)
    payment_type_code = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"Transacción {self.order_id} - {self.status}"


