from django.contrib import admin
from .models import Profile, Job, JobApplication, JobInterest, Notification

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'user_type', 'is_complete', 'company_name']
    list_filter  = ['user_type', 'is_complete']

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'recruiter', 'experience_level', 'is_active', 'created_at']
    list_filter  = ['is_active', 'experience_level']

@admin.register(JobInterest)
class JobInterestAdmin(admin.ModelAdmin):
    list_display = ['freelancer', 'job', 'status', 'created_at']
    list_filter  = ['status']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notif_type', 'title', 'is_read', 'created_at']
    list_filter  = ['notif_type', 'is_read']