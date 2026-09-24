"""
Django admin configuration for the news application.

This module registers the application's models with the Django
administration interface and defines how each model is displayed,
filtered, and searched by administrators.
"""

from django.contrib import admin

from .models import Article, Newsletter, Publisher, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Configure the Django admin interface for the User model."""

    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role", "is_staff")
    search_fields = ("username", "email")


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Configure the Django admin interface for the Publisher model."""

    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Configure the Django admin interface for the Article model."""

    list_display = (
        "title",
        "author",
        "publisher",
        "approved",
        "created_at",
    )

    list_filter = ("approved", "created_at")
    search_fields = ("title", "content")


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Configure the Django admin interface for the Newsletter model."""

    list_display = ("title", "author", "created_at")
    search_fields = ("title", "description")
