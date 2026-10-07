"""
Application configuration for the news application.

This module defines the Django application configuration and loads
the application's signal handlers when Django starts.
"""

from django.apps import AppConfig


class NewsConfig(AppConfig):
    """Configure the Django news application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "news"

    def ready(self):
        """
        Load the news application's signal handlers.

        Importing the signals module registers the post-migrate and
        post-save signal handlers used by the application.
        """
        import news.signals  # noqa: F401
