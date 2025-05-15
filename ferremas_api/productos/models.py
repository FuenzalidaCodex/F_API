from django.db import models

# Create your models here.
class Producto(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=50)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()

    def __str__(self):
        return self.nombre
