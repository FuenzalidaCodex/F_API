from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from .models import Producto, CustomUser, WebPayTransaction, Contacto
from .serializers import ProductoSerializer, CustomUserSerializer, WebPayTransactionSerializer, ContactoSerializer

from django.contrib.auth import authenticate
from rest_framework.response import Response

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from rest_framework import viewsets
from .models import CustomUser
from django.contrib import messages


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


def user_login(request):
    form = AuthenticationForm()   
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Usuario autenticado')
                else: 
                    messages.error(request, 'Usuario no activo')
            else:
                 messages.error(request, 'La información no es correcta')
    else:
        form = AuthenticationForm() 
        messages.error(request, 'Error general')
                
