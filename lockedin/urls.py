"""
URL configuration for lockedin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_old_admin_dashboard(request):
    """Redirect old /admin/dashboard/ URL to new /dashboard/"""
    return redirect('admin_dashboard')

urlpatterns = [
    # Redirect old admin dashboard URL before Django admin catches it
    path('admin/dashboard/', redirect_old_admin_dashboard, name='old_admin_dashboard_redirect'),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('profiles.urls')),
    path('jobs/', include('jobs.urls')),
    path('recruiters/', include('recruiters.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)