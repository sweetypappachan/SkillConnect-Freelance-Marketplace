from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.core.exceptions import ImproperlyConfigured

import threading

from .models import Profile, Job, JobApplication, JobInterest, Notification
from .forms import ProfileForm, FreelancerProfileForm, RecruiterProfileForm, JobForm, JobApplicationForm, JobInterestForm
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives


# ─────────────────────────────────────────
# HELPER: create in-app notification
# ─────────────────────────────────────────
def create_notification(recipient, notif_type, title, message, job=None):
    Notification.objects.create(
        recipient=recipient,
        notif_type=notif_type,
        title=title,
        message=message,
        job=job,
    )


# ─────────────────────────────────────────
# HELPER: send status email to freelancer
# ─────────────────────────────────────────
def send_status_email(freelancer, job, status):
    subject_map = {
        'shortlisted': f"🌟 You've been Shortlisted for {job.title}",
        'accepted':    f"🎉 Congratulations! You've been Accepted for {job.title}",
        'rejected':    f"Update on your application for {job.title}",
    }
    body_map = {
        'shortlisted': (
            f"Hi {freelancer.first_name},\n\n"
            f"Great news! You have been shortlisted for the position of '{job.title}' "
            f"at {job.recruiter.get_full_name() or job.recruiter.username}.\n\n"
            f"The recruiter is reviewing your profile and will be in touch soon.\n\n"
            f"Keep an eye on your SkillConnect dashboard for updates.\n\n"
            f"Best of luck!\nSkillConnect Team"
        ),
        'accepted': (
            f"Hi {freelancer.first_name},\n\n"
            f"Congratulations! 🎉 You have been ACCEPTED for the position of '{job.title}' "
            f"at {job.recruiter.get_full_name() or job.recruiter.username}.\n\n"
            f"The recruiter will contact you shortly. You can also reach them at: {job.recruiter.email}\n\n"
            f"Well done!\nSkillConnect Team"
        ),
        'rejected': (
            f"Hi {freelancer.first_name},\n\n"
            f"Thank you for your interest in '{job.title}'. Unfortunately, the recruiter has decided "
            f"to move forward with other candidates at this time.\n\n"
            f"Don't be discouraged — keep exploring new opportunities on SkillConnect!\n\n"
            f"Best wishes,\nSkillConnect Team"
        ),
    }
    subject = subject_map.get(status, f"Update on your application for {job.title}")
    body    = body_map.get(status, "Your application status has been updated.")

    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [freelancer.email],
            fail_silently=True,
        )
    except Exception:
        pass


# ─────────────────────────────────────────
# HOME
# ─────────────────────────────────────────
def home(request):
    return render(request, "home.html")


# ─────────────────────────────────────────
# SIGNUP
# ─────────────────────────────────────────
def signup(request):
    if request.method == "POST":
        username         = request.POST.get("username")
        email            = request.POST.get("email")
        password         = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        user_type        = request.POST.get("user_type")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("signup")

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user, user_type=user_type)
            messages.success(request, "Account created successfully")
            return redirect("login")
        except Exception:
            messages.error(request, "Something went wrong")
            return redirect("signup")

    return render(request, "accounts/signup.html")


# ─────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user     = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            try:
                profile = Profile.objects.get(user=user)
                if profile.user_type == "freelancer":
                    return redirect("freelancer_dashboard")
                elif profile.user_type == "recruiter":
                    return redirect("recruiter_dashboard")
            except Profile.DoesNotExist:
                messages.error(request, "User profile not found")
                return redirect("login")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


# ─────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


# ─────────────────────────────────────────
# FREELANCER DASHBOARD
# ─────────────────────────────────────────
@login_required
def freelancer_dashboard(request):
    jobs = Job.objects.filter(is_active=True).exclude(recruiter=request.user)

    search = request.GET.get("search")
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(skills_required__icontains=search)
        )

    sort = request.GET.get("sort")
    if sort == "pay":
        jobs = jobs.order_by("-pay_per_hour")
    else:
        jobs = jobs.order_by("-created_at")

    # Build a set of job IDs the user already applied to
    applied_job_ids = set(
        JobInterest.objects.filter(freelancer=request.user).values_list('job_id', flat=True)
    )

    paginator    = Paginator(jobs, 9)
    page_number  = request.GET.get("page")
    page_obj     = paginator.get_page(page_number)

    return render(request, "freelancer_dashboard.html", {
        "page_obj":        page_obj,
        "applied_job_ids": applied_job_ids,
    })


# ─────────────────────────────────────────
# RECRUITER DASHBOARD
# ─────────────────────────────────────────
@login_required
def recruiter_dashboard(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != "recruiter":
        return redirect("freelancer_dashboard")

    jobs = Job.objects.filter(recruiter=request.user, is_active=True).order_by("-created_at")
    return render(request, "recruiter_dashboard.html", {"jobs": jobs})


# ─────────────────────────────────────────
# CREATE JOB
# ─────────────────────────────────────────
@login_required
def create_job(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != "recruiter":
        return redirect("freelancer_dashboard")

    if request.method == "POST":
        Job.objects.create(
            recruiter=request.user,
            title=request.POST.get("title"),
            description=request.POST.get("description"),
            skills_required=request.POST.get("skills_required"),
            tech_stack=request.POST.get("tech_stack"),
            pay_per_hour=request.POST.get("pay_per_hour"),
            experience_level=request.POST.get("experience_level"),
        )
        messages.success(request, "Job posted successfully")
        return redirect("recruiter_dashboard")

    return render(request, "accounts/create_job.html")


# ─────────────────────────────────────────
# CLOSE JOB  (soft-delete: sets is_active=False so it stays in analytics)
# ─────────────────────────────────────────
@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, recruiter=request.user)
    job.is_active = False
    job.save()
    messages.success(request, f"'{job.title}' has been closed and will remain visible in your analytics.")
    return redirect("recruiter_dashboard")


# ─────────────────────────────────────────
# SEND INTEREST  (fixed: notify + guard)
# ─────────────────────────────────────────
@login_required
def send_interest(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if job.recruiter == request.user:
        return redirect("freelancer_dashboard")

    already = JobInterest.objects.filter(job=job, freelancer=request.user).exists()

    if request.method == "POST":
        if already:
            # Return JSON for AJAX or redirect with message
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'already_applied'})
            messages.warning(request, f"You already sent interest for '{job.title}'")
            return redirect("freelancer_dashboard")

        interest = JobInterest.objects.create(job=job, freelancer=request.user)

        # In-app notification for recruiter
        create_notification(
            recipient  = job.recruiter,
            notif_type = 'new_interest',
            title      = f"New Interest: {job.title}",
            message    = f"{request.user.get_full_name() or request.user.username} expressed interest in your job '{job.title}'.",
            job        = job,
        )

        # In-app notification for freelancer (confirmation)
        create_notification(
            recipient  = request.user,
            notif_type = 'interest_sent',
            title      = f"Interest sent for: {job.title}",
            message    = f"You successfully expressed interest in '{job.title}'. Waiting for recruiter response.",
            job        = job,
        )

        # Email to recruiter
        if job.recruiter.email:
            try:
                html_content = render_to_string(
                    "accounts/email_interest.html",
                    {"freelancer": request.user, "job": job}
                )
                email = EmailMultiAlternatives(
                    f"New Interest Received - {job.title}",
                    "",
                    settings.DEFAULT_FROM_EMAIL,
                    [job.recruiter.email],
                )
                email.attach_alternative(html_content, "text/html")
                send_email_async(email)

            except Exception:
                pass

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok'})

        messages.success(request, f"Interest sent for '{job.title}'!")
        return redirect("freelancer_dashboard")

    # GET — shouldn't normally be used; redirect back
    return redirect("freelancer_dashboard")


# ─────────────────────────────────────────
# VIEW INTEREST  (recruiter sees candidates)
# ─────────────────────────────────────────
@login_required
def view_interest(request, job_id):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != "recruiter":
        return redirect("freelancer_dashboard")

    job       = get_object_or_404(Job, id=job_id, recruiter=request.user)
    interests = JobInterest.objects.filter(job=job).select_related('freelancer', 'freelancer__profile')

    return render(request, "view_interest.html", {"job": job, "interests": interests})


# ─────────────────────────────────────────
# UPDATE INTEREST STATUS  (fixed: email + notif)
# ─────────────────────────────────────────
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

@login_required
def update_interest_status(request, interest_id, status):
    interest = get_object_or_404(JobInterest, id=interest_id)

    if interest.job.recruiter != request.user:
        messages.error(request, "Unauthorised action.")
        return redirect("recruiter_dashboard")

    allowed = ['shortlisted', 'accepted', 'rejected', 'pending']
    if status not in allowed:
        messages.error(request, "Invalid status.")
        return redirect("view_interest", job_id=interest.job.id)

    if request.method == "POST":
        old_status      = interest.status
        interest.status = status
        interest.save()

        freelancer = interest.freelancer
        job        = interest.job

        # ── In-app notification for freelancer ──
        notif_titles = {
            'shortlisted': f"You've been shortlisted! 🌟",
            'accepted':    f"Congratulations! You're accepted 🎉",
            'rejected':    f"Application update for {job.title}",
        }
        notif_msgs = {
            'shortlisted': f"Great news! You have been shortlisted for '{job.title}' by {request.user.get_full_name() or request.user.username}. The recruiter will review your profile shortly.",
            'accepted':    f"Congratulations! You have been accepted for '{job.title}' by {request.user.get_full_name() or request.user.username}. They will contact you soon.",
            'rejected':    f"Thank you for your interest in '{job.title}'. The recruiter has decided to move forward with other candidates.",
        }

        if status in notif_titles:
            create_notification(
                recipient  = freelancer,
                notif_type = status,
                title      = notif_titles[status],
                message    = notif_msgs[status],
                job        = job,
            )

        # ── Email to freelancer ──
        if status in ('shortlisted', 'accepted', 'rejected'):

            subject_map = {
                'shortlisted': f"You've been shortlisted for \"{job.title}\"! 🌟",
                'accepted':    f"Congratulations! You're accepted for \"{job.title}\" 🎉",
                'rejected':    f"Application update for \"{job.title}\"",
            }

            badge_map = {
                'shortlisted': '<span style="background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe;padding:6px 20px;border-radius:40px;font-size:13px;font-weight:700;">★ Shortlisted</span>',
                'accepted':    '<span style="background:#eef3e8;color:#3a6e22;border:1px solid #c5ddb1;padding:6px 20px;border-radius:40px;font-size:13px;font-weight:700;">✓ Accepted</span>',
                'rejected':    '<span style="background:#fef2f2;color:#b91c1c;border:1px solid #fecaca;padding:6px 20px;border-radius:40px;font-size:13px;font-weight:700;">✕ Not Selected</span>',
            }

            heading_map = {
                'shortlisted': "You've Been Shortlisted! 🌟",
                'accepted':    "Congratulations! You're Accepted 🎉",
                'rejected':    "Application Update",
            }

            body_map = {
                'shortlisted': "You have been shortlisted for the position below. The recruiter is reviewing your profile and will be in touch soon.",
                'accepted':    "Great news! Your application has been accepted. The recruiter will be reaching out to you shortly.",
                'rejected':    "Thank you for your interest. After careful consideration, the recruiter has decided to move forward with other candidates this time. Don't be discouraged — keep applying!",
            }

            extra_block = ""
            if status == 'accepted':
                extra_block = f"""
                <div style="margin-top:16px;padding:14px;background:#eef3e8;
                border-left:3px solid #8fae74;border-radius:0 8px 8px 0;
                font-size:13px;color:#3a6e22;">
                    The recruiter may contact you at <strong>{freelancer.email}</strong>. Keep an eye on your inbox!
                </div>"""

            html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>SkillConnect</title></head>
<body style="margin:0;padding:0;background-color:#f7f5f0;font-family:Arial,Helvetica,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="padding:30px 0;">
<tr><td align="center">

<table width="600" cellpadding="0" cellspacing="0"
style="background:#ffffff;border-radius:12px;overflow:hidden;
border:1px solid #ece9e0;box-shadow:0 4px 20px rgba(0,0,0,0.05);">

    <tr>
        <td style="background:#111111;color:#8fae74;
        text-align:center;padding:16px;font-size:20px;font-weight:600;">
            SkillConnect
        </td>
    </tr>

    <tr>
        <td style="padding:28px;">

            <div style="font-size:18px;font-weight:600;color:#1a1a1a;margin-bottom:10px;">
                {heading_map[status]}
            </div>

            <div style="margin-bottom:12px;color:#1a1a1a;">
                Hello {freelancer.first_name},
            </div>

            <div style="margin-bottom:20px;color:#777;font-size:14px;">
                {body_map[status]}
            </div>

            <div style="text-align:center;margin-bottom:20px;">
                {badge_map[status]}
            </div>

            <table width="100%" cellpadding="0" cellspacing="0"
            style="background:#f7f5f0;border:1px solid #ece9e0;
            border-radius:10px;padding:16px;">
                <tr>
                    <td style="padding-bottom:10px;font-size:14px;color:#333;">
                        <strong>Job Title:</strong> {job.title}
                    </td>
                </tr>
                <tr>
                    <td style="padding-bottom:10px;font-size:14px;color:#333;">
                        <strong>Recruiter:</strong> {request.user.get_full_name() or request.user.username}
                    </td>
                </tr>
                <tr>
                    <td style="font-size:14px;color:#333;">
                        <strong>Pay:</strong> ₹{job.pay_per_hour}/hr
                    </td>
                </tr>
            </table>

            {extra_block}

            <div style="text-align:center;margin-top:25px;">
                <a href="http://127.0.0.1:8000/freelancer/analytics/"
                style="background:#8fae74;color:#ffffff;padding:12px 28px;
                text-decoration:none;border-radius:30px;font-weight:600;
                font-size:14px;display:inline-block;">
                    View My Applications
                </a>
            </div>

        </td>
    </tr>

    <tr>
        <td style="text-align:center;font-size:12px;color:#777;
        padding:16px;border-top:1px solid #ece9e0;">
            © 2026 SkillConnect — Connecting Talent with Opportunity
        </td>
    </tr>

</table>
</td></tr>
</table>
</body>
</html>"""

            plain_text = f"Hi {freelancer.first_name},\n\nYour application for '{job.title}' has been {status}.\n\n— SkillConnect Team"

            email = EmailMultiAlternatives(
                subject    = subject_map[status],
                body       = plain_text,
                from_email = 'SkillConnect <your@gmail.com>',  # ← change to your Gmail
                to         = [freelancer.email],
            )
            email.attach_alternative(html_content, "text/html")
            send_email_async(email)

        label_map = {'shortlisted': 'Shortlisted', 'accepted': 'Accepted', 'rejected': 'Rejected'}
        messages.success(request, f"{freelancer.first_name} has been {label_map.get(status, status)}.")

    return redirect("view_interest", job_id=interest.job.id)


# ─────────────────────────────────────────
# VIEW FREELANCER PROFILE  (NEW — recruiter can see)
# ─────────────────────────────────────────
@login_required
def view_freelancer_profile(request, user_id):
    recruiter_profile = get_object_or_404(Profile, user=request.user)
    if recruiter_profile.user_type != 'recruiter':
        return redirect("freelancer_dashboard")

    freelancer      = get_object_or_404(User, id=user_id)
    fl_profile      = get_object_or_404(Profile, user=freelancer)

    # Which jobs of this recruiter has the freelancer applied to?
    interests = JobInterest.objects.filter(
        freelancer=freelancer, job__recruiter=request.user
    ).select_related('job')

    return render(request, "freelancer_profile_view.html", {
        "fl_user":    freelancer,
        "fl_profile": fl_profile,
        "interests":  interests,
    })


# ─────────────────────────────────────────
# PROFILE  (fixed: personal info + password)
# ─────────────────────────────────────────
@login_required
def profile(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == "POST":
        action = request.POST.get("action")

        # ── Update personal info ──
        if action == "update_info":
            user = request.user
            user.first_name = request.POST.get("first_name", user.first_name).strip()
            user.last_name  = request.POST.get("last_name",  user.last_name).strip()
            user.email      = request.POST.get("email",      user.email).strip()
            user.save()

            # Update profile fields depending on type
            if profile.user_type == "freelancer":
                profile.education  = request.POST.get("education",  profile.education  or "").strip() or None
                profile.skills     = request.POST.get("skills",     profile.skills     or "").strip() or None
                profile.experience = request.POST.get("experience", profile.experience or "").strip() or None
                profile.about      = request.POST.get("about",      profile.about      or "").strip() or None
                if 'cv' in request.FILES:
                    profile.cv = request.FILES['cv']
            else:
                profile.company_name     = request.POST.get("company_name",     profile.company_name     or "").strip() or None
                profile.company_location = request.POST.get("company_location", profile.company_location or "").strip() or None
                profile.company_website  = request.POST.get("company_website",  profile.company_website  or "").strip() or None
                profile.company_about    = request.POST.get("company_about",    profile.company_about    or "").strip() or None
                profile.recruiter_skills = request.POST.get("recruiter_skills", profile.recruiter_skills or "").strip() or None

            profile.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")

        # ── Change password ──
        if action == "change_password":
            old_password  = request.POST.get("old_password", "")
            new_password  = request.POST.get("new_password", "")
            confirm_pass  = request.POST.get("confirm_password", "")

            if not request.user.check_password(old_password):
                messages.error(request, "Current password is incorrect.")
                return redirect("profile")

            if len(new_password) < 6:
                messages.error(request, "New password must be at least 6 characters.")
                return redirect("profile")

            if new_password != confirm_pass:
                messages.error(request, "New passwords do not match.")
                return redirect("profile")

            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)   # keep user logged in
            messages.success(request, "Password changed successfully!")
            return redirect("profile")

    # Unread notifications for this user
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:20]
    unread_count  = Notification.objects.filter(recipient=request.user, is_read=False).count()

    return render(request, "accounts/profile.html", {
        "profile":        profile,
        "notifications":  notifications,
        "unread_count":   unread_count,
    })


# ─────────────────────────────────────────
# EDIT PROFILE  (legacy — still works)
# ─────────────────────────────────────────
@login_required
def edit_profile(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("profile")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "accounts/edit_profile.html", {"form": form})


# ─────────────────────────────────────────
# NOTIFICATIONS — mark all read  (NEW)
# ─────────────────────────────────────────
@login_required
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


# ─────────────────────────────────────────
# NOTIFICATIONS — count (for bell badge)
# ─────────────────────────────────────────
@login_required
def notification_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})


# ─────────────────────────────────────────
# FREELANCER ANALYTICS  (fixed: pass real data)
# ─────────────────────────────────────────
@login_required
def freelancer_analytics(request):
    interests = JobInterest.objects.filter(freelancer=request.user).select_related('job', 'job__recruiter')

    total_applied  = interests.count()
    shortlisted    = interests.filter(status='shortlisted').count()
    pending        = interests.filter(status='pending').count()
    accepted       = interests.filter(status='accepted').count()
    rejected       = interests.filter(status='rejected').count()

    # Recent 10 for activity feed
    recent_activity = interests.order_by('-created_at')[:10]

    return render(request, "freelancer_analytics.html", {
        "interests":       interests,
        "total_applied":   total_applied,
        "shortlisted":     shortlisted,
        "pending":         pending,
        "accepted":        accepted,
        "rejected":        rejected,
        "recent_activity": recent_activity,
    })


# ─────────────────────────────────────────
# RECRUITER ANALYTICS  (fixed: pass real data)
# ─────────────────────────────────────────
@login_required
def recruiter_analytics(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.user_type != "recruiter":
        return redirect("freelancer_dashboard")

    jobs           = Job.objects.filter(recruiter=request.user)
    total_jobs     = jobs.count()
    active_jobs    = jobs.filter(is_active=True).count()
    closed_jobs    = jobs.filter(is_active=False)

    all_interests  = JobInterest.objects.filter(job__recruiter=request.user)
    total_interests = all_interests.count()
    shortlisted    = all_interests.filter(status='shortlisted').count()
    accepted       = all_interests.filter(status='accepted').count()
    rejected       = all_interests.filter(status='rejected').count()
    reviewed       = shortlisted + accepted + rejected   # anyone whose status changed from pending

    # Top jobs by interest count
    top_jobs = (
        jobs.annotate(interest_count=Count('jobinterest'))
            .order_by('-interest_count')[:5]
    )

    # Recent interests (activity feed)
    recent_interests = all_interests.select_related('freelancer', 'job').order_by('-created_at')[:10]

    return render(request, "recruiter_analytics.html", {
        "total_jobs":       total_jobs,
        "active_jobs":      active_jobs,
        "total_interests":  total_interests,
        "shortlisted":      shortlisted,
        "accepted":         accepted,
        "rejected":         rejected,
        "reviewed":         reviewed,
        "jobs":             jobs,
        "top_jobs":         top_jobs,
        "recent_interests": recent_interests,
        "closed_jobs":      closed_jobs,
    })

try:
    send_mail(
        subject,
        message,
        from_email,
        [recipient],
        fail_silently=True,  # ← Make sure this is True
    )
except Exception:
    pass  # Don't crash if email fails

def send_email_async(email_obj):
    def send():
        try:
            email_obj.send(fail_silently=True)
        except Exception:
            pass
    thread = threading.Thread(target=send)
    thread.daemon = True
    thread.start()