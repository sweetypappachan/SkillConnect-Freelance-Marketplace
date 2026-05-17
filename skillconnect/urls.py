from django.contrib import admin
from django.urls import path, include
from accounts.views import home, login_view, signup, logout_view

from django.conf import settings
from django.conf.urls.static import static

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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)