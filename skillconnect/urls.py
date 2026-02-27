from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import (
    home,
    login_view,
    signup_page,
    dashboard,
    logout_user,
    freelancer_setup,
    recruiter_setup,
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home (Landing + Login)
    path('', home, name='home'),

    # Authentication
    path('login/', login_view, name='login'),
    path('signup/', signup_page, name='signup'),
    path('logout/', logout_user, name='logout'),

    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # Setup Pages
    path('freelancer/setup/', freelancer_setup, name='freelancer_setup'),
    path('recruiter/setup/', recruiter_setup, name='recruiter_setup'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)