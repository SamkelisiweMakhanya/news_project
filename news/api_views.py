"""REST API views and role-based permissions."""

import secrets
from typing import ClassVar

from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, Newsletter, Publisher, User
from .serializers import (
    ApprovedArticleSerializer,
    ArticleSerializer,
    NewsletterSerializer,
    PublisherSerializer,
    UserSerializer,
)


class IsEditorOrJournalist(permissions.BasePermission):
    """Allow write operations to editors and journalists."""

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.role in (User.Role.EDITOR, User.Role.JOURNALIST)
        )


class IsJournalist(permissions.BasePermission):
    """Allow creation only to journalists."""

    def has_permission(self, request, view):
        return bool(
            request.user.is_authenticated
            and request.user.role == User.Role.JOURNALIST
        )


class ArticleListCreateView(generics.ListCreateAPIView):
    """List articles or let journalists create articles."""

    serializer_class = ArticleSerializer

    def get_queryset(self):
        # The public article collection contains approved stories only.
        return Article.objects.filter(approved=True).select_related(
            "author", "publisher"
        ).order_by("-created_at")

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsJournalist()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, approved=False)


class SubscribedArticlesView(APIView):
    """Return approved articles from the reader's subscriptions."""

    permission_classes: ClassVar[list] = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.READER:
            return Response(
                {"detail": "Only readers can access subscribed articles."},
                status=403,
            )
        articles = Article.objects.filter(approved=True).filter(
            publisher__in=request.user.subscribed_publishers.all()
        ) | Article.objects.filter(
            approved=True, author__in=request.user.subscribed_journalists.all()
        )
        serializer = ArticleSerializer(
            articles.select_related("author", "publisher").distinct(),
            many=True,
        )
        return Response(serializer.data)


class ArticleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an article."""

    serializer_class = ArticleSerializer

    def get_queryset(self):
        queryset = Article.objects.select_related("author", "publisher")
        if self.request.user.role == User.Role.READER:
            queryset = queryset.filter(approved=True)
        return queryset

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsEditorOrJournalist()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        instance = serializer.instance
        if (
            self.request.user.role == User.Role.JOURNALIST
            and instance.author_id != self.request.user.id
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Journalists can only edit their own articles."
            )
        serializer.save(
            approved=(
                False
                if self.request.user.role == User.Role.JOURNALIST
                else instance.approved
            )
        )

    def perform_destroy(self, instance):
        if (
            self.request.user.role == User.Role.JOURNALIST
            and instance.author_id != self.request.user.id
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Journalists can only delete their own articles."
            )
        instance.delete()


class ApprovedArticleView(APIView):
    """Accept audit notifications for articles already approved in the DB."""

    # The endpoint uses a shared secret rather than a user token.
    permission_classes: ClassVar[list] = [AllowAny]

    def post(self, request):
        expected_secret = settings.APPROVED_ARTICLE_API_SECRET
        supplied_secret = request.headers.get(
            "X-Internal-API-Secret", ""
        )

        if (
            not expected_secret
            or not supplied_secret
            or not secrets.compare_digest(
                supplied_secret, expected_secret
            )
        ):
            raise PermissionDenied("Invalid internal API credentials.")

        article_id = request.data.get("id")

        if not article_id:
            return Response(
                {"detail": "An article ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            article = Article.objects.select_related(
                "author", "publisher"
            ).get(pk=article_id, approved=True)
        except (Article.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": "No approved article matches this ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = ApprovedArticleSerializer(instance=article)

        return Response(
            {
                "message": "Approved article verified successfully.",
                "article": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class NewsletterListCreateView(generics.ListCreateAPIView):
    """List newsletters or create one as a journalist/editor."""

    serializer_class = NewsletterSerializer

    def get_queryset(self):
        return (
            Newsletter.objects.select_related("author")
            .prefetch_related("articles")
            .order_by("-created_at")
        )

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsEditorOrJournalist()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class NewsletterDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a newsletter."""

    serializer_class = NewsletterSerializer

    def get_queryset(self):
        return (
            Newsletter.objects.select_related("author")
            .prefetch_related("articles")
        )

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsEditorOrJournalist()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        if (
            self.request.user.role == User.Role.JOURNALIST
            and serializer.instance.author_id != self.request.user.id
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Journalists can only edit their own newsletters."
            )
        serializer.save()

    def perform_destroy(self, instance):
        if (
            self.request.user.role == User.Role.JOURNALIST
            and instance.author_id != self.request.user.id
        ):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied(
                "Journalists can only delete their own newsletters."
            )
        instance.delete()


class PublisherListView(generics.ListCreateAPIView):
    """List publishers and allow editors to create them."""

    queryset = Publisher.objects.all().prefetch_related("members")
    serializer_class = PublisherSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        if self.request.user.role != User.Role.EDITOR:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only editors can create publishers.")
        serializer.save()


class PublisherDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage a publisher."""

    queryset = Publisher.objects.all().prefetch_related("members")
    serializer_class = PublisherSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def check_editor(self):
        if self.request.user.role != User.Role.EDITOR:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only editors can manage publishers.")

    def perform_update(self, serializer):
        self.check_editor()
        serializer.save()

    def perform_destroy(self, instance):
        self.check_editor()
        instance.delete()


class UserDetailView(generics.RetrieveAPIView):
    """Return the authenticated user's public API profile."""

    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user
