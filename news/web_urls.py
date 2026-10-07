"""URL configuration for the web-facing application."""

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views import (
    approve_article,
    article_create,
    article_delete,
    article_detail,
    article_edit,
    article_list,
    article_review,
    feed,
    home,
    newsletter_create,
    newsletter_delete,
    newsletter_detail,
    newsletter_edit,
    newsletter_list,
    publisher_create,
    publisher_delete,
    publisher_edit,
    publisher_list,
    register,
    subscriptions,
    update_subscriptions,
)

urlpatterns = [
    path("", home, name="home"),
    path("register/", register, name="register"),
    path(
        "accounts/login/",
        LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("articles/", article_list, name="article-list"),
    path("articles/new/", article_create, name="article-create"),
    path("articles/<int:article_id>/", article_detail, name="article-detail"),
    path("articles/<int:article_id>/edit/", article_edit, name="article-edit"),
    path(
        "articles/<int:article_id>/delete/",
        article_delete,
        name="article-delete",
    ),
    path("articles/review/", article_review, name="article-review"),
    path(
        "articles/<int:article_id>/approve/",
        approve_article,
        name="approve-article",
    ),
    path("newsletters/", newsletter_list, name="newsletter-list"),
    path("newsletters/new/", newsletter_create, name="newsletter-create"),
    path(
        "newsletters/<int:newsletter_id>/",
        newsletter_detail,
        name="newsletter-detail",
    ),
    path(
        "newsletters/<int:newsletter_id>/edit/",
        newsletter_edit,
        name="newsletter-edit",
    ),
    path(
        "newsletters/<int:newsletter_id>/delete/",
        newsletter_delete,
        name="newsletter-delete",
    ),
    path("subscriptions/", subscriptions, name="subscriptions"),
    path(
        "subscriptions/update/",
        update_subscriptions,
        name="update-subscriptions",
    ),
    path("feed/", feed, name="feed"),
    path("publishers/", publisher_list, name="publisher-list"),
    path("publishers/new/", publisher_create, name="publisher-create"),
    path(
        "publishers/<int:publisher_id>/edit/",
        publisher_edit,
        name="publisher-edit",
    ),
    path(
        "publishers/<int:publisher_id>/delete/",
        publisher_delete,
        name="publisher-delete",
    ),
]
