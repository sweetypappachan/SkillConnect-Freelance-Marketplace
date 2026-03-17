from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.core.paginator import Paginator
from django.db.models import Q

from .models import Profile, Job, JobApplication

from .models import JobInterest





# -------------------------
# HOME PAGE
# -------------------------
def home(request):
    return render(request, "home.html")


# -------------------------
# SIGNUP
# -------------------------
def signup(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        user_type = request.POST.get("user_type")

        # Password match check
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        # Username exists check
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")

        # Email exists check (recommended)
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("signup")

        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            # Create profile
            Profile.objects.create(
                user=user,
                user_type=user_type
            )

            messages.success(request, "Account created successfully")
            return redirect("login")

        except Exception as e:
            messages.error(request, "Something went wrong")
            return redirect("signup")

    return render(request, "accounts/signup.html")


# -------------------------
# LOGIN
# -------------------------
def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:

            login(request, user)

            try:
                profile = Profile.objects.get(user=user)

                if profile.user_type == "freelancer":
                    return redirect("freelancer_dashboard")

                elif profile.user_type == "recruiter":
                    return redirect("recruiter_dashboard")

                else:
                    messages.error(request, "Invalid user type")
                    return redirect("login")

            except Profile.DoesNotExist:
                messages.error(request, "User profile not found")
                return redirect("login")

        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


# -------------------------
# LOGOUT
# -------------------------
@login_required
def logout_view(request):

    logout(request)
    return redirect("login")


# -------------------------
# FREELANCER DASHBOARD
# -------------------------
@login_required
def freelancer_dashboard(request):

    jobs = Job.objects.filter(is_active=True).exclude(recruiter=request.user)

    # search
    search = request.GET.get("search")
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(skills_required__icontains=search)
        )

    # sorting
    sort = request.GET.get("sort")

    if sort == "pay":
        jobs = jobs.order_by("-pay_per_hour")
    else:
        jobs = jobs.order_by("-created_at")

    # pagination (6 jobs per page)
    paginator = Paginator(jobs, 9)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "freelancer_dashboard.html", {"page_obj": page_obj})


# -------------------------
# RECRUITER DASHBOARD
# -------------------------
@login_required
def recruiter_dashboard(request):

    profile = Profile.objects.get(user=request.user)

    if profile.user_type != "recruiter":
        return redirect("freelancer_dashboard")

    jobs = Job.objects.filter(recruiter=request.user).order_by("-created_at")

    context = {
    "jobs": jobs
     }

    return render(request, "recruiter_dashboard.html", context)



# -------------------------
# JOB LIST FOR FREELANCER
# ------------------------
@login_required
def job_list(request):

    jobs = Job.objects.filter(is_active=True)

    context = {
        "jobs": jobs
    }

    return render(request, "job_list.html", context)


# -------------------------
# APPLY JOB
# -------------------------
@login_required
def apply_job(request, job_id):

    profile = Profile.objects.get(user=request.user)

    if profile.user_type != "freelancer":
        return redirect("recruiter_dashboard")

    job = get_object_or_404(Job, id=job_id)

    if JobApplication.objects.filter(job=job, freelancer=request.user).exists():
        messages.warning(request, "You already applied for this job")
        return redirect("freelancer_dashboard")

    if request.method == "POST":

        cover_letter = request.POST.get("cover_letter")

        JobApplication.objects.create(
            job=job,
            freelancer=request.user,
            cover_letter=cover_letter
        )

        messages.success(request, "Application submitted")

        return redirect("freelancer_dashboard")

    context = {
        "job": job
    }

    return render(request, "apply_job.html", context)

# -------------------------
# VIEW APPLICATIONS (RECRUITER)
# -------------------------
@login_required
def view_applications(request, job_id):

    # Get logged in user profile
    profile = get_object_or_404(Profile, user=request.user)

    # Only recruiter can view applications
    if profile.user_type != "recruiter":
        return redirect("freelancer_dashboard")

    # Get the job posted by this recruiter
    job = get_object_or_404(Job, id=job_id, recruiter=request.user)

    # Get applications for this job
    applications = JobApplication.objects.filter(job=job)

    context = {
        "job": job,
        "applications": applications
    }

    return render(request, "view_applications.html", context)


# -------------------------
# PROFILE PAGE
# -------------------------
@login_required
def profile(request):

    profile = get_object_or_404(Profile, user=request.user)

    context = {
        "profile": profile
    }

    return render(request, "accounts/profile.html", context)


@login_required
def create_job(request):
    profile = Profile.objects.get(user=request.user)

    if profile.user_type != "recruiter":
        return redirect("freelancer_dashboard")

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        skills = request.POST.get("skills_required")
        tech = request.POST.get("tech_stack")
        pay = request.POST.get("pay_per_hour")
        level = request.POST.get("experience_level")

        Job.objects.create(
            recruiter=request.user,
            title=title,
            description=description,
            skills_required=skills,
            tech_stack=tech,
            pay_per_hour=pay,
            experience_level=level
            )

        messages.success(request, "Job posted successfully")
        return redirect("recruiter_dashboard")

    return render(request, "accounts/create_job.html")





from django.shortcuts import get_object_or_404, redirect

@login_required
def delete_job(request, job_id):

    job = get_object_or_404(Job, id=job_id, recruiter=request.user)
    job.delete()

    return redirect('recruiter_dashboard')




@login_required
def send_interest(request, job_id):

    job = get_object_or_404(Job, id=job_id)

    # prevent recruiter sending to own job
    if job.recruiter == request.user:
        return redirect("freelancer_dashboard")

    # prevent duplicate interest
    if not JobInterest.objects.filter(job=job, freelancer=request.user).exists():

        JobInterest.objects.create(
            job=job,
            freelancer=request.user
        )

    return redirect("freelancer_dashboard")

# -------------------------
# VIEW INTERESTS (RECRUITER)
# -------------------------
@login_required
def view_interest(request, job_id):

    profile = get_object_or_404(Profile, user=request.user)

    # Only recruiter allowed
    if profile.user_type != "recruiter":
        return redirect("freelancer_dashboard")

    job = get_object_or_404(Job, id=job_id, recruiter=request.user)

    interests = JobInterest.objects.filter(job=job)

    context = {
        "job": job,
        "interests": interests
    }

    return render(request, "view_interest.html", context)