"""
URL configuration for the article review and approval workflow.

This module maps article review and approval endpoints to their
corresponding view functions.
"""

from django.contrib.auth.views import LoginView
from django.urls import path

from .views import approve_article, article_review, home

urlpatterns = [
    # Display articles that are available for review.
    path("", home, name="home"),

   path(
    "accounts/login/",
        LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),

    path(
        "articles/review/",
        article_review,
        name="article-review",
    ),

    # Approve a specific article using its primary key.
    path(
        "articles/<int:article_id>/approve/",
        approve_article,
        name="approve-article",
    ),
]
