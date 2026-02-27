from django.urls import path
from .views import FreelancerRegisterView, RecruiterRegisterView

urlpatterns = [
    path('register/freelancer/', FreelancerRegisterView.as_view(), name='register_freelancer'),
    path('register/recruiter/', RecruiterRegisterView.as_view(), name='register_recruiter'),
]