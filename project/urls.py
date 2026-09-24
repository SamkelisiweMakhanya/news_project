"""
URL configuration for the Django project.

This module defines the URL routes for the application, including the
Django administration site, API authentication, REST API endpoints,
and web-facing application pages.
"""

from django.contrib import admin
from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # Django administration site.
    path("admin/", admin.site.urls),

    # API endpoint for obtaining an authentication token.
    path("api/token/", obtain_auth_token, name="api-token"),

    # REST API endpoints provided by the news application.
    path("api/", include("news.urls")),

    # Web pages provided by the news application.
    path("", include("news.web_urls")),
]
