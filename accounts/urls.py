from django.urls import path
from . import views

urlpatterns = [
    # ── Auth ──
    path('signup/',  views.signup,       name='signup'),
    path('login/',   views.login_view,   name='login'),
    path('logout/',  views.logout_view,  name='logout'),

    # ── Home ──
    path('',         views.home,         name='home'),

    # ── Dashboards ──
    path('freelancer/dashboard/', views.freelancer_dashboard, name='freelancer_dashboard'),
    path('recruiter/dashboard/',  views.recruiter_dashboard,  name='recruiter_dashboard'),

    # ── Analytics ──
    path('freelancer/analytics/', views.freelancer_analytics, name='freelancer_analytics'),
    path('recruiter/analytics/',  views.recruiter_analytics,  name='recruiter_analytics'),

    # ── Jobs ──
    path('create-job/',              views.create_job,  name='create_job'),
    path('delete-job/<int:job_id>/', views.delete_job,  name='delete_job'),

    # ── Interests ──
    path('send-interest/<int:job_id>/',  views.send_interest,  name='send_interest'),
    path('view-interest/<int:job_id>/',  views.view_interest,  name='view_interest'),
    path(
        'update-interest-status/<int:interest_id>/<str:status>/',
        views.update_interest_status,
        name='update_interest_status',
    ),

    # ── Profile ──
    path('profile/',      views.profile,      name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),

    # ── NEW: Recruiter views freelancer profile ──
    path(
        'freelancer/<int:user_id>/profile/',
        views.view_freelancer_profile,
        name='view_freelancer_profile',
    ),

    # ── NEW: Notifications ──
    path('notifications/mark-read/',  views.mark_notifications_read, name='mark_notifications_read'),
    path('notifications/count/',      views.notification_count,      name='notification_count'),
]