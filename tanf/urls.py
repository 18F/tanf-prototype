"""tanf URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from uaa_client.decorators import staff_login_required

# Wrap the admin site login with our staff_login_required decorator,
# which will raise a PermissionDenied exception if a logged-in, but
# non-staff user attempts to access the login page.
admin.site.login = staff_login_required(admin.site.login)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('uaa_client.urls')),
    path('', include('upload.urls')),
]
