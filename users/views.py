from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from django.http import HttpResponse

User = get_user_model()


def home(request):
    return HttpResponse("Welcome to SkillConnect Dashboard")

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        role = request.POST.get("role")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 == password2:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            user.phone = phone
            user.role = role
            user.save()
            return redirect("login")

    return render(request, "users/register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")

    return render(request, "users/login.html")