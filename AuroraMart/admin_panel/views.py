from django.shortcuts import render
from django.http import HttpResponse

def login(request):
    return render(request, 'admin_panel/login.html')

def signup(request):
    return render(request, 'admin_panel/signup.html')

def index(request):
    return render(request, 'admin_panel/index.html')


