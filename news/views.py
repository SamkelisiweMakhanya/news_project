"""Views for the role-based web interface."""

from functools import wraps

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .forms import ArticleForm, NewsletterForm, PublisherForm, RegistrationForm
from .models import Article, Newsletter, Publisher, User

UserModel = get_user_model()


def role_required(*roles):
    """Restrict a view to authenticated users with specific roles."""

    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                return render(
                    request,
                    "news/forbidden.html",
                    status=403,
                )
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


def home(request):
    """Show approved stories and a personalised feed for readers."""
    articles = Article.objects.filter(approved=True).select_related(
        "author", "publisher"
    ).order_by("-created_at")
    feed = None
    if request.user.is_authenticated and request.user.role == User.Role.READER:
        feed = articles.filter(
            Q(publisher__in=request.user.subscribed_publishers.all())
            | Q(author__in=request.user.subscribed_journalists.all())
        ).distinct()[:10]
    return render(request, "news/home.html", {
        "approved_articles": articles[:8], "feed": feed,
    })


def register(request):
    """Register and sign in a new user."""
    if request.user.is_authenticated:
        return redirect("home")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account has been created.")
        return redirect("home")
    return render(request, "registration/register.html", {"form": form})


@login_required
def article_list(request):
    """List all approved articles for readers and all articles for staff."""
    qs = (
        Article.objects.select_related("author", "publisher")
        .order_by("-created_at")
    )
    if request.user.role == User.Role.READER:
        qs = qs.filter(approved=True)
    return render(request, "news/article_list.html", {"articles": qs})


@login_required
def article_detail(request, article_id):
    """Display one article."""
    article = get_object_or_404(
        Article.objects.select_related("author", "publisher"),
        pk=article_id,
    )
    if request.user.role == User.Role.READER and not article.approved:
        return render(request, "news/forbidden.html", status=403)
    return render(request, "news/article_detail.html", {"article": article})


@login_required
@role_required(User.Role.JOURNALIST)
def article_create(request):
    article = Article(author=request.user)

    if request.method == "POST":
        form = ArticleForm(
            request.POST,
            instance=article,
            user=request.user,
        )

        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            messages.success(request, "Article created successfully.")
            return redirect("article-list")
    else:
        form = ArticleForm(
            instance=article,
            user=request.user,
        )

    return render(
        request,
        "news/article_form.html",
        {"form": form},
    )


@role_required(User.Role.JOURNALIST, User.Role.EDITOR)
def article_edit(request, article_id):
    """Edit an article."""
    article = get_object_or_404(Article, pk=article_id)
    if (
        request.user.role == User.Role.JOURNALIST
        and article.author_id != request.user.id
    ):
        return render(request, "news/forbidden.html", status=403)
    form = ArticleForm(
        request.POST or None,
        instance=article,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        changed = form.save(commit=False)
        if request.user.role == User.Role.JOURNALIST:
            changed.approved = False
        changed.save()
        messages.success(request, "Article updated.")
        return redirect("article-detail", article.id)
    return render(
        request,
        "news/article_form.html",
        {"form": form, "heading": "Edit article"},
    )


@role_required(User.Role.JOURNALIST, User.Role.EDITOR)
@require_POST
def article_delete(request, article_id):
    """Delete an article."""
    article = get_object_or_404(Article, pk=article_id)
    if (
        request.user.role == User.Role.JOURNALIST
        and article.author_id != request.user.id
    ):
        return render(request, "news/forbidden.html", status=403)
    article.delete()
    messages.success(request, "Article deleted.")
    return redirect("article-list")


@role_required(User.Role.EDITOR)
def article_review(request):
    """Show the editor approval queue."""
    articles = (
        Article.objects.filter(approved=False)
        .select_related("author", "publisher")
    )
    return render(request, "news/article_review.html", {"articles": articles})


@role_required(User.Role.EDITOR)
@require_POST
def approve_article(request, article_id):
    """Approve an article, notify subscribers, and POST an audit record."""
    article = get_object_or_404(
        Article,
        pk=article_id,
        approved=False,
    )
    article.approved = True
    article.save(update_fields=["approved"])

    if article.publisher_id:
        subscribers = UserModel.objects.filter(
            subscribed_publishers=article.publisher
        )
    else:
        subscribers = UserModel.objects.filter(
            subscribed_journalists=article.author
        )
    emails = list(
        subscribers.exclude(email="").values_list("email", flat=True)
    )
    if emails:
        send_mail(
            f"New approved article: {article.title}",
            f"{article.title}\n\n{article.content}",
            settings.DEFAULT_FROM_EMAIL,
            recipient_list=emails,
            fail_silently=True,
        )
    try:
        response = requests.post(
            request.build_absolute_uri("/api/approved/"),
            json={
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "author": article.author_id,
                "publisher": article.publisher_id,
                "approved": True,
                "created_at": article.created_at.isoformat(),
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        messages.warning(
            request,
            "Article approved, but API audit logging was unavailable.",
        )
    messages.success(request, "Article approved successfully.")
    return redirect("article-review")


@login_required
def newsletter_list(request):
    """List newsletters."""
    newsletters = (
        Newsletter.objects.select_related("author")
        .prefetch_related("articles")
        .order_by("-created_at")
    )
    return render(
        request,
        "news/newsletter_list.html",
        {"newsletters": newsletters},
    )


@login_required
def newsletter_detail(request, newsletter_id):
    """Display a newsletter."""
    newsletter = get_object_or_404(
        Newsletter.objects.prefetch_related("articles"),
        pk=newsletter_id,
    )
    return render(
        request,
        "news/newsletter_detail.html",
        {"newsletter": newsletter},
    )


@role_required(User.Role.JOURNALIST, User.Role.EDITOR)
def newsletter_create(request):
    """Create a newsletter."""
    form = NewsletterForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        newsletter = form.save(commit=False)
        newsletter.author = request.user
        newsletter.save()
        form.save_m2m()
        messages.success(request, "Newsletter created.")
        return redirect("newsletter-detail", newsletter.id)
    return render(
        request,
        "news/newsletter_form.html",
        {"form": form, "heading": "Create newsletter"},
    )


@role_required(User.Role.JOURNALIST, User.Role.EDITOR)
def newsletter_edit(request, newsletter_id):
    """Edit a newsletter."""
    newsletter = get_object_or_404(Newsletter, pk=newsletter_id)
    if (
        request.user.role == User.Role.JOURNALIST
        and newsletter.author_id != request.user.id
    ):
        return render(request, "news/forbidden.html", status=403)
    form = NewsletterForm(
        request.POST or None,
        instance=newsletter,
        user=request.user,
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Newsletter updated.")
        return redirect("newsletter-detail", newsletter.id)
    return render(
        request,
        "news/newsletter_form.html",
        {"form": form, "heading": "Edit newsletter"},
    )


@role_required(User.Role.JOURNALIST, User.Role.EDITOR)
@require_POST
def newsletter_delete(request, newsletter_id):
    """Delete a newsletter."""
    newsletter = get_object_or_404(Newsletter, pk=newsletter_id)
    if (
        request.user.role == User.Role.JOURNALIST
        and newsletter.author_id != request.user.id
    ):
        return render(request, "news/forbidden.html", status=403)
    newsletter.delete()
    messages.success(request, "Newsletter deleted.")
    return redirect("newsletter-list")


@role_required(User.Role.READER)
def subscriptions(request):
    """Manage reader subscriptions to publishers and journalists."""
    publishers = Publisher.objects.all().order_by("name")
    journalists = UserModel.objects.filter(
        role=User.Role.JOURNALIST
    ).order_by("username")
    return render(
        request,
        "news/subscriptions.html",
        {"publishers": publishers, "journalists": journalists},
    )


@role_required(User.Role.READER)
@require_POST
def update_subscriptions(request):
    """Replace the reader's publisher and journalist subscriptions."""
    publisher_ids = request.POST.getlist("publishers")
    journalist_ids = request.POST.getlist("journalists")
    request.user.subscribed_publishers.set(
        Publisher.objects.filter(pk__in=publisher_ids)
    )
    request.user.subscribed_journalists.set(
        UserModel.objects.filter(
            pk__in=journalist_ids,
            role=User.Role.JOURNALIST,
        )
    )
    messages.success(request, "Subscriptions updated.")
    return redirect("subscriptions")


@role_required(User.Role.READER)
def feed(request):
    """Display personalised content from subscriptions."""
    articles = (
        Article.objects.filter(approved=True)
        .filter(
            Q(publisher__in=request.user.subscribed_publishers.all())
            | Q(author__in=request.user.subscribed_journalists.all())
        )
        .select_related("author", "publisher")
        .distinct()
        .order_by("-created_at")
    )
    return render(request, "news/feed.html", {"articles": articles})


@role_required(User.Role.EDITOR)
def publisher_list(request):
    """List publishers."""
    publishers = Publisher.objects.prefetch_related("members")
    return render(
        request,
        "news/publisher_list.html",
        {"publishers": publishers},
    )


@role_required(User.Role.EDITOR)
def publisher_create(request):
    """Create a publisher."""
    form = PublisherForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Publisher created.")
        return redirect("publisher-list")
    return render(
        request,
        "news/publisher_form.html",
        {"form": form, "heading": "Create publisher"},
    )


@role_required(User.Role.EDITOR)
def publisher_edit(request, publisher_id):
    """Update a publisher and its linked staff."""
    publisher = get_object_or_404(Publisher, pk=publisher_id)
    form = PublisherForm(request.POST or None, instance=publisher)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Publisher updated.")
        return redirect("publisher-list")
    return render(
        request,
        "news/publisher_form.html",
        {"form": form, "heading": "Edit publisher"},
    )


@role_required(User.Role.EDITOR)
@require_POST
def publisher_delete(request, publisher_id):
    """Delete a publisher."""
    get_object_or_404(Publisher, pk=publisher_id).delete()
    messages.success(request, "Publisher deleted.")
    return redirect("publisher-list")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def publishers(request):
    """Return publishers as JSON for API clients."""
    data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
        }
        for p in Publisher.objects.all()
    ]
    return Response({"publishers": data})
