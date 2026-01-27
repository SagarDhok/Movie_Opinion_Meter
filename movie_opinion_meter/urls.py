"""
URL configuration for movie_opinion_meter project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from movies.admin_sync import sync_tmdb



urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('', include('movies.urls')),
    path("api/", include("movies.api.urls")),
    path("admin/sync-tmdb/", sync_tmdb),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# If DEBUG=True (development mode), Django will serve uploaded files by linking MEDIA_URL (/media/)
# to the actual folder path MEDIA_ROOT (media/ directory)

#  ✅ we use static() here because it creates URL routes automatically to serve files.

# Why static() is used?

# ✅ It tells Django:

# “If someone opens /media/... then go to MEDIA_ROOT folder and return that file.”

# So without static() your uploaded image/file will not open in browser during development.

