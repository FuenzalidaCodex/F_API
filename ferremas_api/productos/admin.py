from django.contrib import admin
from .models import Producto, Categoria_Producto, Ferretería, CustomUser, WebPayTransaction, Contacto

admin.site.register(Producto)
admin.site.register(Categoria_Producto)
admin.site.register(Ferretería)
admin.site.register(CustomUser)
admin.site.register(WebPayTransaction)
admin.site.register(Contacto)