from django import forms
from .models import Profile, Job, JobApplication, JobInterest


class FreelancerProfileForm(forms.ModelForm):
    class Meta:
        model  = Profile
        fields = ['education', 'skills', 'experience', 'cv', 'about']


class RecruiterProfileForm(forms.ModelForm):
    class Meta:
        model  = Profile
        fields = [
            'company_name',
            'company_location',
            'company_website',
            'company_about',
            'recruiter_skills',
        ]


# Keep the old generic form for backward compat (used in edit_profile)
class ProfileForm(forms.ModelForm):
    class Meta:
        model  = Profile
        fields = [
            'user_type',
            'education',
            'skills',
            'experience',
            'cv',
            'company_name',
            'company_location',
            'company_website',
            'company_about',
            'recruiter_skills',
            'about',
        ]


class JobForm(forms.ModelForm):
    class Meta:
        model  = Job
        fields = [
            'title',
            'description',
            'skills_required',
            'tech_stack',
            'pay_per_hour',
            'experience_level',
        ]


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model  = JobApplication
        fields = ['cover_letter']


class JobInterestForm(forms.ModelForm):
    class Meta:
        model  = JobInterest
        fields = ['message']