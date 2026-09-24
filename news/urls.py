"""
URL configuration for the news application's API.

This module maps API endpoints to the appropriate views for managing
articles, subscribed articles, approved articles, and newsletters.
"""

from django.urls import path

from .api_views import (
    ApprovedArticleView,
    ArticleDetailView,
    ArticleListCreateView,
    NewsletterDetailView,
    NewsletterListCreateView,
    SubscribedArticlesView,
)

urlpatterns = [
    # List articles or create a new article.
    path(
        "articles/",
        ArticleListCreateView.as_view(),
        name="article-list-create",
    ),

    # Return articles from the reader's subscriptions.
    path(
        "articles/subscribed/",
        SubscribedArticlesView.as_view(),
        name="subscribed-articles",
    ),

    # Retrieve, update, or delete an individual article.
    path(
        "articles/<int:pk>/",
        ArticleDetailView.as_view(),
        name="article-detail",
    ),

    # Receive an approved article through the API.
    path(
        "approved/",
        ApprovedArticleView.as_view(),
        name="approved-article",
    ),

    # List newsletters or create a new newsletter.
    path(
        "newsletters/",
        NewsletterListCreateView.as_view(),
        name="newsletter-list-create",
    ),

    # Retrieve, update, or delete an individual newsletter.
    path(
        "newsletters/<int:pk>/",
        NewsletterDetailView.as_view(),
        name="newsletter-detail",
    ),
]
