from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Profile


# =====================================
# HOME PAGE (Landing Page Only)
# =====================================
def home(request):
    return render(request, "home.html")


# =====================================
# LOGIN PAGE
# =====================================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            profile, created = Profile.objects.get_or_create(user=user)

            if not profile.is_complete:
                if profile.user_type == "freelancer":
                    return redirect("freelancer_setup")
                else:
                    return redirect("recruiter_setup")

            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")


# =====================================
# SIGNUP PAGE
# =====================================
def signup_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        user_type = request.POST.get("user_type")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")

        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )

        Profile.objects.create(
            user=user,
            user_type=user_type,
            is_complete=False
        )

        messages.success(request, "Account created successfully. Please login.")
        return redirect("login")

    return render(request, "signup.html")


# =====================================
# FREELANCER SETUP
# =====================================
def freelancer_setup(request):
    if not request.user.is_authenticated:
        return redirect("login")

    profile = Profile.objects.get(user=request.user)

    if profile.is_complete:
        return redirect("dashboard")

    if request.method == "POST":
        profile.education = request.POST.get("education")
        profile.skills = request.POST.get("skills")
        profile.experience = request.POST.get("experience")

        if request.FILES.get("cv"):
            profile.cv = request.FILES.get("cv")

        profile.is_complete = True
        profile.save()

        messages.success(request, "Profile completed successfully!")
        return redirect("dashboard")

    return render(request, "freelancer_setup.html")


# =====================================
# RECRUITER SETUP
# =====================================
def recruiter_setup(request):
    if not request.user.is_authenticated:
        return redirect("login")

    profile = Profile.objects.get(user=request.user)

    if profile.is_complete:
        return redirect("dashboard")

    if request.method == "POST":
        profile.company_name = request.POST.get("company_name")
        profile.job_title = request.POST.get("job_title")
        profile.job_description = request.POST.get("job_description")
        profile.salary = request.POST.get("salary")

        profile.is_complete = True
        profile.save()

        messages.success(request, "Job details saved successfully!")
        return redirect("dashboard")

    return render(request, "recruiter_setup.html")


# =====================================
# DASHBOARD
# =====================================
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")

    profile = Profile.objects.get(user=request.user)

    if not profile.is_complete:
        if profile.user_type == "freelancer":
            return redirect("freelancer_setup")
        else:
            return redirect("recruiter_setup")

    if profile.user_type == "freelancer":
        return render(request, "freelancer_dashboard.html", {"profile": profile})
    else:
        return render(request, "recruiter_dashboard.html", {"profile": profile})


# =====================================
# LOGOUT
# =====================================
def logout_user(request):
    logout(request)
    return redirect("home")