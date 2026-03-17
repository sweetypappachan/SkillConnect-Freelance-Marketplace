from django.urls import path
from . import views

urlpatterns = [

    path('signup/', views.signup, name='signup'),

    path('login/', views.login_view, name='login'),

    path('logout/', views.logout_view, name='logout'),

    path('freelancer/dashboard/', views.freelancer_dashboard, name='freelancer_dashboard'),

    path('recruiter/dashboard/', views.recruiter_dashboard, name='recruiter_dashboard'),

    path('create-job/', views.create_job, name='create_job'),

    path('profile/', views.profile, name='profile'),

    path('delete-job/<int:job_id>/', views.delete_job, name='delete_job'),

    path('send-interest/<int:job_id>/', views.send_interest, name='send_interest'),

    path('view-interest/<int:job_id>/', views.view_interest, name='view_interest'),

]