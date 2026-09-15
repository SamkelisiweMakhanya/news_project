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
    path(
        "articles/",
        ArticleListCreateView.as_view(),
        name="article-list-create",
    ),
    path(
        "articles/subscribed/",
        SubscribedArticlesView.as_view(),
        name="subscribed-articles",
    ),
    path(
        "articles/<int:pk>/",
        ArticleDetailView.as_view(),
        name="article-detail",
    ),

    path(
        "approved/",
        ApprovedArticleView.as_view(),
        name="approved-article",
    ),

    path(
        "newsletters/",
        NewsletterListCreateView.as_view(),
        name="newsletter-list-create",
    ),

    path(
        "newsletters/<int:pk>/",
        NewsletterDetailView.as_view(),
        name="newsletter-detail",
    ),
]
