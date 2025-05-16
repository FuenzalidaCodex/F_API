from django.db import models

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



