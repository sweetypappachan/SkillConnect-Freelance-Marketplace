from django.contrib import admin
from django.urls import path, include
from accounts.views import home, login_view, signup, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # Home
    path('', home, name='home'),

    # Authentication
    path('login/', login_view, name='login'),
    path('signup/', signup, name='signup'),
    path('logout/', logout_view, name='logout'),

    # Accounts app URLs
    path('', include('accounts.urls')),
]