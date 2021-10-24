from django.shortcuts import render
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


class Login(LoginView):
    success_url = reverse_lazy('adusersapp:index')
    template_name = 'users/login.html'
