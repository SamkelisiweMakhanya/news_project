"""
Views for the news article review and approval workflow.

This module provides views for editors to review articles, approve
articles, notify subscribers by email, and send approved article
data to the application's API endpoint.
"""

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Article, User


def home(request):
    """
    Display the landing page for the news application.
    """
    return render(request, "news/home.html")


@login_required
def article_review(request):
    """
    Display articles that are waiting for editor approval.

    Only authenticated users with the Editor role can access the
    article review page.
    """

    if request.user.role != User.Role.EDITOR:
        return render(
            request,
            "news/forbidden.html",
            status=403,
        )

    articles = (
        Article.objects
        .filter(approved=False)
        .select_related("author", "publisher")
        .order_by("-created_at")
    )

    return render(
        request,
        "news/article_review.html",
        {"articles": articles},
    )


@login_required
@require_POST
def approve_article(request, article_id):
    """
    Approve an article and notify its subscribers.

    The approved article is saved, subscribers are notified by email,
    and the approved article data is sent to the application's API.
    """

    if request.user.role != User.Role.EDITOR:
        return render(
            request,
            "news/forbidden.html",
            status=403,
        )

    article = get_object_or_404(
        Article,
        pk=article_id,
    )

    article.approved = True
    article.save(update_fields=["approved"])

    if article.publisher:
        subscribers = User.objects.filter(
            subscribed_publishers=article.publisher,
        )
    else:
        subscribers = User.objects.filter(
            subscribed_journalists=article.author,
        )

    email_addresses = list(
        subscribers.values_list("email", flat=True)
    )

    if email_addresses:
        send_mail(
            subject=f"New approved article: {article.title}",
            message=(
                f"{article.title}\n\n"
                f"{article.content}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=email_addresses,
            fail_silently=True,
        )

    api_url = request.build_absolute_uri("/api/approved/")

    try:
        response = requests.post(
            api_url,
            json={
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "author": article.author.id,
                "publisher": (
                    article.publisher.id
                    if article.publisher
                    else None
                ),
                "approved": article.approved,
                "created_at": article.created_at.isoformat(),
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        pass

    messages.success(
        request,
        "Article approved successfully.",
    )

    return redirect("article-review")
